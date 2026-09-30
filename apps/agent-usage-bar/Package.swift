// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "UsageBar",
    platforms: [.macOS(.v14)],
    products: [.executable(name: "usagebar", targets: ["UsageBar"])],
    targets: [.executableTarget(name: "UsageBar")]
)
