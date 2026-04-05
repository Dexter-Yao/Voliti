// ABOUTME: MIRROR 页统一事件流区域
// ABOUTME: 日折叠、过滤器联动、里程碑缩略图、周边界粗线

import SwiftUI

struct EventStreamSection: View {
    let groups: [(date: Date, events: [BehaviorEvent])]
    let isExpanded: (Date) -> Bool
    let toggleExpanded: (Date) -> Void
    let eventCount: (Date) -> Int
    let cardLookup: (String) -> InterventionCard?
    var onCardTap: ((InterventionCard) -> Void)?

    var body: some View {
        LazyVStack(alignment: .leading, spacing: 0) {
            ForEach(Array(groups.enumerated()), id: \.element.date) { index, group in
                if isExpanded(group.date) {
                    expandedDay(group: group, index: index)
                } else {
                    collapsedDay(date: group.date, count: group.events.count)
                }

                if isWeekBoundary(at: index) {
                    StarpathDivider(opacity: 0.15, thickness: 2)
                        .padding(.horizontal, StarpathTokens.spacingMD)
                }
            }
        }
    }

    // MARK: - Expanded Day

    private func expandedDay(group: (date: Date, events: [BehaviorEvent]), index: Int) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            dayHeader(date: group.date, count: group.events.count, canCollapse: canCollapse(group.date))
                .padding(.top, index == 0 ? 0 : StarpathTokens.spacingLG)
                .padding(.bottom, StarpathTokens.spacingSM)

            ForEach(group.events, id: \.id) { event in
                eventRow(event)
                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)
            }
        }
    }

    private func eventRow(_ event: BehaviorEvent) -> some View {
        Group {
            if event.type == .signatureImage, let cardId = event.cardId,
               let card = cardLookup(cardId) {
                milestoneRow(event: event, card: card)
            } else {
                EventRow(event: event)
                    .padding(.horizontal, StarpathTokens.spacingMD)
            }
        }
    }

    private func milestoneRow(event: BehaviorEvent, card: InterventionCard) -> some View {
        Button {
            onCardTap?(card)
        } label: {
            HStack(spacing: StarpathTokens.spacingMD) {
                if let imageData = card.imageData, let uiImage = UIImage(data: imageData) {
                    Image(uiImage: uiImage)
                        .resizable()
                        .scaledToFill()
                        .frame(width: 48, height: 48)
                        .clipped()
                } else {
                    Rectangle()
                        .fill(StarpathTokens.obsidian10)
                        .frame(width: 48, height: 48)
                }

                VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(event.type.label)
                            .starpathSans()
                        Spacer()
                        Text(event.timestamp, style: .time)
                            .starpathMono()
                    }
                    if let summary = event.summary, !summary.isEmpty {
                        Text(summary)
                            .starpathSans()
                            .foregroundStyle(StarpathTokens.obsidian)
                    }
                }
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
            .padding(.vertical, StarpathTokens.spacingSM)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Collapsed Day

    private func collapsedDay(date: Date, count: Int) -> some View {
        Button {
            toggleExpanded(date)
        } label: {
            HStack {
                Text(date, format: .dateTime.month().day())
                    .starpathSans()
                Text("·")
                    .foregroundStyle(StarpathTokens.obsidian40)
                Text("\(count) 条记录")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian40)
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: StarpathTokens.fontSizeXS))
                    .foregroundStyle(StarpathTokens.obsidian40)
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
            .padding(.vertical, StarpathTokens.spacingSM)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Day Header

    private func dayHeader(date: Date, count: Int, canCollapse: Bool) -> some View {
        Button {
            if canCollapse { toggleExpanded(date) }
        } label: {
            HStack {
                Text(dayLabel(date))
                    .starpathSerif()
                if canCollapse {
                    Image(systemName: "chevron.down")
                        .font(.system(size: StarpathTokens.fontSizeXS))
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
                Spacer()
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
        }
        .buttonStyle(.plain)
        .disabled(!canCollapse)
    }

    // MARK: - Helpers

    private func canCollapse(_ date: Date) -> Bool {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        let yesterday = calendar.date(byAdding: .day, value: -1, to: today)!
        return date < yesterday
    }

    private func dayLabel(_ date: Date) -> String {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        if date == today { return "今天" }
        let yesterday = calendar.date(byAdding: .day, value: -1, to: today)!
        if date == yesterday { return "昨天" }
        let formatter = DateFormatter()
        formatter.dateFormat = "M月d日"
        return formatter.string(from: date)
    }

    private func isWeekBoundary(at index: Int) -> Bool {
        guard index + 1 < groups.count else { return false }
        let calendar = Calendar.current
        let currentWeek = calendar.component(.weekOfYear, from: groups[index].date)
        let nextWeek = calendar.component(.weekOfYear, from: groups[index + 1].date)
        return currentWeek != nextWeek
    }
}
