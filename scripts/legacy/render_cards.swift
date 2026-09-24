#!/usr/bin/env swift
import AppKit
import Foundation

struct Dimensions: Codable { let width: Int; let height: Int }
struct Point: Codable { let label: String; let text: String }
struct Table: Codable { let headers: [String]; let rows: [[String]] }
struct Chart: Codable { let kind: String; let labels: [String]; let values: [Double] }
struct Card: Codable {
    let id: String
    let type: String
    let title: String
    let prompt: String?
    let blanks: [String]?
    let answerKey: [String]?
    let definition: String?
    let points: [Point]?
    let table: Table?
    let chart: Chart?
    let takeaway: String?
    let tags: [String]?
    enum CodingKeys: String, CodingKey {
        case id, type, title, prompt, blanks, definition, points, table, chart, takeaway, tags
        case answerKey = "answer_key"
    }
}
struct Manifest: Codable {
    let title: String
    let topics: [String]
    let caption: String
    let dimensions: Dimensions
    let cards: [Card]
}

extension NSColor {
    convenience init(hex: String) {
        var value = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        if value.count == 6 { value = "FF" + value }
        var number: UInt64 = 0
        Scanner(string: value).scanHexInt64(&number)
        self.init(red: CGFloat((number >> 16) & 0xFF) / 255.0,
                  green: CGFloat((number >> 8) & 0xFF) / 255.0,
                  blue: CGFloat(number & 0xFF) / 255.0,
                  alpha: CGFloat((number >> 24) & 0xFF) / 255.0)
    }
}

let theme: [String: String] = [
    "background": "#F7F8FA", "ink": "#17202A", "muted": "#5C6773",
    "accent": "#246BFD", "accentSoft": "#E8F0FF"
]
let args = CommandLine.arguments
guard args.count == 3 else {
    fputs("usage: render_cards.swift MANIFEST OUTPUT_DIR\n", stderr)
    exit(2)
}
let manifestURL = URL(fileURLWithPath: args[1])
let outputURL = URL(fileURLWithPath: args[2], isDirectory: true)
let manifest: Manifest
do {
    manifest = try JSONDecoder().decode(Manifest.self, from: Data(contentsOf: manifestURL))
} catch {
    fputs("manifest decode failed: \(error)\n", stderr)
    exit(2)
}

func font(_ size: CGFloat, bold: Bool = false) -> NSFont {
    return NSFont(name: bold ? "PingFangSC-Semibold" : "PingFangSC-Regular", size: size)
        ?? NSFont.systemFont(ofSize: size, weight: bold ? .semibold : .regular)
}

func drawText(_ text: String, in rect: CGRect, size: CGFloat, color: NSColor, bold: Bool = false, alignment: NSTextAlignment = .left) {
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = alignment
    paragraph.lineBreakMode = .byWordWrapping
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font(size, bold: bold), .foregroundColor: color, .paragraphStyle: paragraph
    ]
    (text as NSString).draw(in: rect, withAttributes: attributes)
}

func fillRounded(_ rect: CGRect, color: NSColor, radius: CGFloat = 16, stroke: NSColor? = nil, lineWidth: CGFloat = 1) {
    let path = NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
    color.setFill(); path.fill()
    if let stroke {
        stroke.setStroke(); path.lineWidth = lineWidth; path.stroke()
    }
}

func makeImage(for card: Card, width: Int, height: Int) -> NSBitmapImageRep {
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
                               bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                               isPlanar: false, colorSpaceName: .deviceRGB,
                               bitmapFormat: [], bytesPerRow: 0, bitsPerPixel: 0)!
    let context = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = context
    let w = CGFloat(width), h = CGFloat(height), margin: CGFloat = 72
    NSColor(hex: theme["background"]!).setFill(); NSRect(x: 0, y: 0, width: w, height: h).fill()
    let ink = NSColor(hex: theme["ink"]!), muted = NSColor(hex: theme["muted"]!), accent = NSColor(hex: theme["accent"]!), soft = NSColor(hex: theme["accentSoft"]!)
    fillRounded(CGRect(x: margin, y: h - 114, width: 180, height: 42), color: soft, radius: 21)
    drawText(card.type == "quick_check" ? "快速填空" : "知识讲解", in: CGRect(x: margin + 20, y: h - 104, width: 140, height: 24), size: 20, color: accent, bold: true)
    drawText(card.title, in: CGRect(x: margin, y: h - 275, width: w - margin * 2, height: 120), size: 48, color: ink, bold: true)
    var y = h - 350
    if card.type == "quick_check" {
        drawText(card.prompt ?? "", in: CGRect(x: margin, y: y - 125, width: w - margin * 2, height: 125), size: 30, color: ink)
        y -= 210
        for (index, blank) in (card.blanks ?? []).prefix(6).enumerated() {
            let x = margin + CGFloat(index % 2) * 470
            let yy = y - CGFloat(index / 2) * 132
            fillRounded(CGRect(x: x, y: yy, width: 390, height: 84), color: .white, radius: 14, stroke: accent, lineWidth: 3)
            drawText("\(index + 1). \(blank.isEmpty ? "填写" : blank)", in: CGRect(x: x + 24, y: yy + 25, width: 342, height: 36), size: 26, color: muted)
        }
        y -= CGFloat(((card.blanks ?? []).prefix(6).count + 1) / 2) * 132 + 30
        drawText("先独立回忆，再对照答案。", in: CGRect(x: margin, y: y - 30, width: w - margin * 2, height: 30), size: 24, color: muted)
    } else {
        if let definition = card.definition {
            drawText("定义", in: CGRect(x: margin, y: y - 32, width: 200, height: 28), size: 22, color: accent, bold: true)
            drawText(definition, in: CGRect(x: margin, y: y - 165, width: w - margin * 2, height: 120), size: 28, color: ink)
            y -= 205
        }
        for point in (card.points ?? []).prefix(5) {
            accent.setFill(); NSBezierPath(ovalIn: CGRect(x: margin + 6, y: y - 20, width: 20, height: 20)).fill()
            drawText("\(point.label)：\(point.text)", in: CGRect(x: margin + 48, y: y - 74, width: w - margin * 2 - 48, height: 74), size: 26, color: ink)
            y -= 104
        }
        if let table = card.table {
            drawText("关系表", in: CGRect(x: margin, y: y - 32, width: 200, height: 28), size: 22, color: accent, bold: true)
            y -= 70
            let cols = max(1, table.headers.count), colWidth = (w - margin * 2) / CGFloat(cols)
            let rows = [table.headers] + Array(table.rows.prefix(5))
            for (rowIndex, row) in rows.enumerated() {
                let rowRect = CGRect(x: margin, y: y - 62, width: w - margin * 2, height: 62)
                fillRounded(rowRect, color: rowIndex == 0 ? soft : .white, radius: 3, stroke: NSColor(hex: "#D9E0EA"))
                for (colIndex, cell) in row.prefix(cols).enumerated() {
                    drawText(cell, in: CGRect(x: margin + CGFloat(colIndex) * colWidth + 10, y: y - 52, width: colWidth - 20, height: 42), size: 19, color: ink, bold: rowIndex == 0)
                }
                y -= 62
            }
        }
        if let chart = card.chart {
            drawText("趋势图", in: CGRect(x: margin, y: y - 32, width: 200, height: 28), size: 22, color: accent, bold: true)
            y -= 70
            let maxValue = max(chart.values.max() ?? 1, 1)
            for (index, label) in chart.labels.prefix(4).enumerated() {
                let value = index < chart.values.count ? chart.values[index] : 0
                let barWidth = CGFloat(520.0 * value / maxValue)
                drawText(label, in: CGRect(x: margin, y: y - 28, width: 90, height: 24), size: 18, color: ink)
                fillRounded(CGRect(x: margin + 108, y: y - 25, width: barWidth, height: 24), color: accent, radius: 12)
                y -= 48
            }
        }
        if let takeaway = card.takeaway {
            let box = CGRect(x: margin, y: max(120, y - 110), width: w - margin * 2, height: 100)
            fillRounded(box, color: soft, radius: 16)
            drawText(takeaway, in: CGRect(x: box.minX + 26, y: box.minY + 18, width: box.width - 52, height: 64), size: 24, color: ink, bold: true)
        }
    }
    drawText("CRASH FLASHCARD · 秋招速记", in: CGRect(x: margin, y: 38, width: w - margin * 2, height: 26), size: 18, color: muted, bold: true)
    NSGraphicsContext.restoreGraphicsState()
    return rep
}

let fm = FileManager.default
for card in manifest.cards {
    let folderName = card.type == "quick_check" ? "quick-check" : "explanation"
    let folder = outputURL.appendingPathComponent(folderName, isDirectory: true)
    try? fm.createDirectory(at: folder, withIntermediateDirectories: true)
    let image = makeImage(for: card, width: manifest.dimensions.width, height: manifest.dimensions.height)
    guard let data = image.representation(using: .png, properties: [:]) else {
        fputs("could not encode PNG for \(card.id)\n", stderr)
        exit(2)
    }
    do {
        try data.write(to: folder.appendingPathComponent("\(card.id).png"), options: .atomic)
    } catch {
        fputs("could not write PNG for \(card.id): \(error)\n", stderr)
        exit(2)
    }
}
