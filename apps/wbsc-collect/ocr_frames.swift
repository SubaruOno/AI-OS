// 静止画をまとめて Mac の文字認識（Vision、韓国語と英語）にかける。kbo_clips.py から使う。
//
//     ocr_frames <画像> [<画像> ...]
//
// 1枚につき1行の JSON（{"file": ..., "lines": [{"text": ..., "x": ..., "y": ..., "w": ..., "h": ...}]}）を出す。
// 位置は画像の左上を0とした 0〜1 の割合。

import AppKit
import Foundation
import Vision

func recognize(_ path: String) -> [[String: Any]] {
    guard let img = NSImage(contentsOfFile: path) else { return [] }
    var rect = NSRect(x: 0, y: 0, width: img.size.width, height: img.size.height)
    guard let cg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil) else { return [] }
    let req = VNRecognizeTextRequest()
    req.recognitionLanguages = ["ko-KR", "en-US"]
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    do { try VNImageRequestHandler(cgImage: cg).perform([req]) } catch { return [] }
    return (req.results ?? []).compactMap { obs in
        guard let top = obs.topCandidates(1).first else { return nil }
        let b = obs.boundingBox
        return ["text": top.string, "x": b.minX, "y": 1 - b.maxY, "w": b.width, "h": b.height]
    }
}

for path in CommandLine.arguments.dropFirst() {
    let row: [String: Any] = ["file": path, "lines": recognize(path)]
    if let data = try? JSONSerialization.data(withJSONObject: row),
       let s = String(data: data, encoding: .utf8) {
        print(s)
    }
}
