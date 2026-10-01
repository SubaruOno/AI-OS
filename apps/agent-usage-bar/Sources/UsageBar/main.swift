import AppKit
import SwiftUI
import Security
import Darwin
import SQLite3

struct UsageWindow: Decodable {
    var utilization: Double?
    var resets_at: String?
}
struct ClaudeUsage: Decodable {
    var five_hour: UsageWindow?
    var seven_day: UsageWindow?
    var seven_day_sonnet: UsageWindow?
}
struct CodexWindow: Decodable {
    var usedPercent: Double?
    var windowDurationMins: Int?
    var resetsAt: Double?
}
struct CodexLimits: Decodable {
    var primary: CodexWindow?
    var secondary: CodexWindow?
}
struct AppServerMessage: Decodable {
    var id: Int?
    var result: RateLimitResult?
    var error: ServerError?
}
struct RateLimitResult: Decodable {
    var rateLimits: CodexLimits?
}
struct ServerError: Decodable { var message: String? }

struct WindowView: Identifiable {
    let id: String
    let title: String
    let percent: Double
    let reset: Date?
}
struct ProviderView: Identifiable {
    let id: String
    let name: String
    let status: String
    var windows: [WindowView]
}

final class HTTPResponseBox: @unchecked Sendable {
    private let lock = NSLock()
    private var responseData: Data?
    private var responseStatus = 0
    func store(data: Data?, status: Int) {
        lock.lock(); defer { lock.unlock() }
        responseData = data; responseStatus = status
    }
    func load() -> (Data?, Int) {
        lock.lock(); defer { lock.unlock() }
        return (responseData, responseStatus)
    }
}

enum UsageLog {
    static func write(_ message: String) {
        let url = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/AgentUsageBar.log")
        let line = "\(ISO8601DateFormatter().string(from: Date())) \(message)\n"
        guard let data = line.data(using: .utf8) else { return }
        try? FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        if FileManager.default.fileExists(atPath: url.path), let handle = try? FileHandle(forWritingTo: url) {
            _ = try? handle.seekToEnd(); try? handle.write(contentsOf: data); try? handle.close()
        } else { try? data.write(to: url) }
    }
}

@MainActor final class UsageModel: ObservableObject {
    @Published var providers = [ProviderView]()
    @Published var refreshedAt: Date?
    @Published var refreshing = false
    private var timer: Timer?
    init() {
        refresh()
        timer = Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { [weak self] _ in Task { @MainActor in self?.refresh() } }
        NotificationCenter.default.addObserver(forName: .init("UsageBarDidRefresh"), object: nil, queue: .main) { [weak self] _ in
            Task { @MainActor in self?.objectWillChange.send() }
        }
    }
    func refresh() {
        guard !refreshing else { return }
        refreshing = true
        UsageLog.write("refresh started")
        providers = [
            ProviderView(id: "claude", name: "Claude Code", status: "取得中", windows: []),
            ProviderView(id: "codex", name: "Codex", status: "取得中", windows: []),
            ProviderView(id: "opencode", name: "OpenCode", status: "取得中", windows: [])
        ]
        DispatchQueue.global(qos: .utility).async { [weak self] in
            let group = DispatchGroup()
            let lock = NSLock()
            var results = [String: ProviderView]()
            for (id, read) in [("claude", Self.readClaude), ("codex", Self.readCodex), ("opencode", Self.readOpenCode)] {
                group.enter()
                DispatchQueue.global(qos: .utility).async {
                    let result = read()
                    UsageLog.write("\(id) finished: \(result.status.isEmpty ? "ok" : result.status)")
                    lock.lock(); results[id] = result; lock.unlock()
                    DispatchQueue.main.async { [weak self] in
                        guard let self else { return }
                        lock.lock(); let current = results; lock.unlock()
                        self.providers = [current["claude"], current["codex"], current["opencode"]].compactMap { $0 }
                        NotificationCenter.default.post(name: .init("UsageBarDidRefresh"), object: nil)
                    }
                    group.leave()
                }
            }
            group.notify(queue: .main) { [weak self] in
                Task { @MainActor in
                    guard let self else { return }
                    self.refreshedAt = Date()
                    self.refreshing = false
                    UsageLog.write("refresh completed")
                }
            }
        }
    }
    nonisolated private static func readClaude() -> ProviderView {
        let auth = ProcessResult.run("/usr/bin/security", ["find-generic-password", "-s", "Claude Code-credentials", "-w"])
        guard auth.status == 0, let bytes = auth.output.data(using: .utf8),
              let root = try? JSONSerialization.jsonObject(with: bytes) as? [String: Any],
              let oauth = root["claudeAiOauth"] as? [String: Any],
              let token = oauth["accessToken"] as? String else {
            return ProviderView(id: "claude", name: "Claude Code", status: "Claude CodeのKeychainログインが見つかりません", windows: [])
        }
        let request = NSMutableURLRequest(url: URL(string: "https://api.anthropic.com/api/oauth/usage")!)
        request.httpMethod = "GET"
        request.timeoutInterval = 12
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("claude-code/2.1.59", forHTTPHeaderField: "User-Agent")
        request.setValue("oauth-2025-04-20", forHTTPHeaderField: "anthropic-beta")
        let semaphore = DispatchSemaphore(value: 0)
        let responseBox = HTTPResponseBox()
        URLSession.shared.dataTask(with: request as URLRequest) { d, response, _ in
            responseBox.store(data: d, status: (response as? HTTPURLResponse)?.statusCode ?? 0)
            semaphore.signal()
        }.resume()
        guard semaphore.wait(timeout: .now() + 15) == .success else {
            return ProviderView(id: "claude", name: "Claude Code", status: "Anthropicへの接続がタイムアウトしました", windows: [])
        }
        let (data, statusCode) = responseBox.load()
        guard (200..<300).contains(statusCode), let data,
              let usage = try? JSONDecoder().decode(ClaudeUsage.self, from: data) else {
            let msg = statusCode == 401 ? "ログイン期限切れ。Claude Codeを一度開いてください" : "使用量を取得できません (HTTP \(statusCode))"
            return ProviderView(id: "claude", name: "Claude Code", status: msg, windows: [])
        }
        var windows = [WindowView]()
        for (id, title, window) in [("5h", "5時間", usage.five_hour), ("week", "週", usage.seven_day), ("sonnet", "Sonnet週", usage.seven_day_sonnet)] {
            if let window, let percent = window.utilization {
                windows.append(WindowView(id: id, title: title, percent: percent, reset: window.resets_at.flatMap { ISO8601DateFormatter().date(from: $0) }))
            }
        }
        return ProviderView(id: "claude", name: "Claude Code", status: windows.isEmpty ? "サブスクリプション利用枠がありません" : "", windows: windows)
    }
    nonisolated private static func readCodex() -> ProviderView {
        UsageLog.write("codex locating CLI")
        guard let path = executable("codex") else { return ProviderView(id: "codex", name: "Codex", status: "Codex CLIが見つかりません", windows: []) }
        UsageLog.write("codex CLI: \(path)")
        let process = Process()
        process.executableURL = URL(fileURLWithPath: path)
        process.arguments = ["app-server", "--stdio"]
        let input = Pipe(), output = Pipe()
        process.standardInput = input; process.standardOutput = output; process.standardError = FileHandle.nullDevice
        do { try process.run() } catch { return ProviderView(id: "codex", name: "Codex", status: "Codex app-serverを起動できません", windows: []) }
        defer { if process.isRunning { process.terminate() } }
        UsageLog.write("codex app-server started")
        let writer = input.fileHandleForWriting
        let reader = output.fileHandleForReading
        func send(_ value: [String: Any]) {
            guard let bytes = try? JSONSerialization.data(withJSONObject: value), var line = String(data: bytes, encoding: .utf8) else { return }
            line += "\n"; writer.write(Data(line.utf8))
        }
        send(["method":"initialize", "id":1, "params":["clientInfo":["name":"UsageBar", "version":"1.0"], "capabilities":[:]]])
        UsageLog.write("codex initialize sent")
        var buffer = Data()
        func nextLine(until deadline: Date) -> Data? {
            while Date() < deadline {
                if let range = buffer.range(of: Data([10])) {
                    let line = buffer.subdata(in: 0..<range.lowerBound); buffer.removeSubrange(0..<range.upperBound); return line
                }
                var descriptor = pollfd(fd: reader.fileDescriptor, events: Int16(POLLIN), revents: 0)
                let remaining = max(1, Int32(deadline.timeIntervalSinceNow * 1000))
                let ready = poll(&descriptor, 1, min(remaining, 250))
                if ready > 0, descriptor.revents & Int16(POLLIN) != 0 {
                    var bytes = [UInt8](repeating: 0, count: 4096)
                    let count = Darwin.read(reader.fileDescriptor, &bytes, bytes.count)
                    if count > 0 { buffer.append(contentsOf: bytes.prefix(count)) }
                    else { return nil }
                } else if ready > 0, descriptor.revents & (Int16(POLLHUP) | Int16(POLLERR)) != 0 {
                    return nil
                }
            }
            return nil
        }
        let initEnd = Date().addingTimeInterval(8)
        var initialized = false
        while let line = nextLine(until: initEnd) {
            if let m = try? JSONDecoder().decode(AppServerMessage.self, from: line), m.id == 1 { initialized = true; break }
        }
        guard initialized else { return ProviderView(id: "codex", name: "Codex", status: "Codex app-serverの応答がありません", windows: []) }
        UsageLog.write("codex initialized")
        send(["method":"initialized", "params":[:]])
        send(["method":"account/rateLimits/read", "id":2, "params":[:]])
        UsageLog.write("codex rate limits requested")
        let end = Date().addingTimeInterval(8)
        while let line = nextLine(until: end) {
            guard let m = try? JSONDecoder().decode(AppServerMessage.self, from: line), m.id == 2 else { continue }
            guard let limits = m.result?.rateLimits else { return ProviderView(id: "codex", name: "Codex", status: m.error?.message ?? "Codex利用枠を取得できません", windows: []) }
            var windows = [WindowView]()
            if let w = limits.primary, let p = w.usedPercent { windows.append(WindowView(id: "5h", title: "5時間", percent: p, reset: w.resetsAt.map { Date(timeIntervalSince1970: $0) })) }
            if let w = limits.secondary, let p = w.usedPercent { windows.append(WindowView(id: "week", title: "週", percent: p, reset: w.resetsAt.map { Date(timeIntervalSince1970: $0) })) }
            return ProviderView(id: "codex", name: "Codex", status: "", windows: windows)
        }
        return ProviderView(id: "codex", name: "Codex", status: "Codex利用枠の応答がありません", windows: [])
    }
    nonisolated private static func readOpenCode() -> ProviderView {
        let db = NSHomeDirectory() + "/.local/share/opencode/opencode.db"
        var handle: OpaquePointer?
        guard sqlite3_open_v2(db, &handle, SQLITE_OPEN_READONLY | SQLITE_OPEN_NOMUTEX, nil) == SQLITE_OK, let handle else {
            return ProviderView(id: "opencode", name: "OpenCode", status: "OpenCodeの利用記録が見つかりません", windows: [])
        }
        defer { sqlite3_close(handle) }
        var stmt: OpaquePointer?
        let sql = "SELECT COUNT(*), COALESCE(SUM(time_updated),0), COALESCE(MAX(time_updated),0) FROM session"
        guard sqlite3_prepare_v2(handle, sql, -1, &stmt, nil) == SQLITE_OK, let stmt else {
            return ProviderView(id: "opencode", name: "OpenCode", status: "利用記録を読み取れません", windows: [])
        }
        defer { sqlite3_finalize(stmt) }
        guard sqlite3_step(stmt) == SQLITE_ROW else { return ProviderView(id: "opencode", name: "OpenCode", status: "利用記録を読み取れません", windows: []) }
        let count = sqlite3_column_int(stmt, 0)
        let newest = sqlite3_column_int64(stmt, 2)
        let last = newest > 10_000_000_000 ? Date(timeIntervalSince1970: Double(newest) / 1000) : Date(timeIntervalSince1970: Double(newest))
        let label = count == 0 ? "セッション記録なし" : "\(count)セッション · 最終利用 \(RelativeDateTimeFormatter().localizedString(for: last, relativeTo: Date()))"
        return ProviderView(id: "opencode", name: "OpenCode", status: label + "\nプロバイダー利用枠・リセット時刻はローカル履歴にありません", windows: [])
    }
    nonisolated private static func executable(_ name: String) -> String? {
        guard name == "codex" else { return nil }
        let candidates = ["/opt/homebrew/bin/codex", "/usr/local/bin/codex", "/usr/bin/codex"]
        return candidates.first { FileManager.default.isExecutableFile(atPath: $0) }
    }
}

struct ProcessResult {
    let status: Int32
    let output: String
    static func run(_ executable: String, _ arguments: [String]) -> ProcessResult {
        let p = Process(), pipe = Pipe()
        p.executableURL = URL(fileURLWithPath: executable); p.arguments = arguments
        p.standardOutput = pipe; p.standardError = Pipe()
        do { try p.run() } catch { return ProcessResult(status: -1, output: "") }
        let data = pipe.fileHandleForReading.readDataToEndOfFile(); p.waitUntilExit()
        return ProcessResult(status: p.terminationStatus, output: String(data: data, encoding: .utf8) ?? "")
    }
}

struct PopoverView: View {
    @ObservedObject var model: UsageModel
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack { Text("AI Usage").font(.headline); Spacer(); Button { model.refresh() } label: { Image(systemName: "arrow.clockwise") }.disabled(model.refreshing) }
            ForEach(model.providers) { provider in
                VStack(alignment: .leading, spacing: 7) {
                    Text(provider.name).font(.system(size: 14, weight: .semibold))
                    if !provider.windows.isEmpty {
                        ForEach(provider.windows) { window in
                            HStack(spacing: 8) {
                                Text(window.title).frame(width: 62, alignment: .leading)
                                ProgressView(value: min(max(window.percent, 0), 100), total: 100).frame(width: 112)
                                Text("\(Int(window.percent.rounded()))%").monospacedDigit().frame(width: 39, alignment: .trailing)
                                if let reset = window.reset { Text("あと\(reset, style: .relative)").font(.caption).foregroundStyle(.secondary).frame(width: 64, alignment: .trailing) }
                            }.font(.system(size: 12))
                        }
                    }
                    if !provider.status.isEmpty { Text(provider.status).font(.caption).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true) }
                }
                if provider.id != model.providers.last?.id { Divider() }
            }
            HStack { Text(model.refreshedAt.map { "更新 \($0.formatted(date: .omitted, time: .shortened))" } ?? "取得中").font(.caption2).foregroundStyle(.tertiary); Spacer(); Button("終了") { NSApplication.shared.terminate(nil) }.buttonStyle(.plain).font(.caption).foregroundStyle(.secondary) }
        }.padding(14).frame(width: 360)
    }
}

@MainActor final class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private let model = UsageModel()
    private var popover: NSPopover!
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.image = NSImage(systemSymbolName: "gauge.with.dots.needle.67percent", accessibilityDescription: "AI usage")
        statusItem.button?.imagePosition = .imageOnly
        statusItem.button?.action = #selector(togglePopover)
        statusItem.button?.target = self
        popover = NSPopover(); popover.behavior = .transient; popover.contentSize = NSSize(width: 360, height: 340)
        popover.contentViewController = NSHostingController(rootView: PopoverView(model: model))
        model.$providers.sink { [weak self] providers in
            Task { @MainActor in
                let percent = providers.flatMap(\.windows).map(\.percent).max().map { Int($0.rounded()) }
                self?.statusItem.button?.toolTip = percent.map { "AIの残り \($0)%" } ?? "AI usage"
                NotificationCenter.default.post(name: .init("UsageBarDidRefresh"), object: nil)
            }
        }.store(in: &subscriptions)
    }
    private var subscriptions = Set<AnyCancellable>()
    @objc private func togglePopover() {
        guard let button = statusItem.button else { return }
        if popover.isShown { popover.performClose(nil) } else { model.refresh(); popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY) }
    }
}

import Combine
let app = NSApplication.shared
MainActor.assumeIsolated {
    let delegate = AppDelegate()
    app.delegate = delegate
    app.run()
}
