// ABOUTME: MIRROR 页事件流过滤器，单选 pill 按钮组
// ABOUTME: 过滤器映射：全部/时刻（moment）/数据（weighIn, stateCheckin）/饮食（meal, waterIntake）

import SwiftUI

enum EventFilter: String, CaseIterable {
    case all = "全部"
    case moment = "时刻"
    case data = "数据"
    case diet = "饮食"

    var matchingTypes: Set<EventType>? {
        switch self {
        case .all: nil
        case .moment: [.moment]
        case .data: [.weighIn, .stateCheckin]
        case .diet: [.meal, .waterIntake]
        }
    }

    func matches(_ event: BehaviorEvent) -> Bool {
        guard let types = matchingTypes else { return true }
        return types.contains(event.type)
    }
}

struct FilterBar: View {
    @Binding var selected: EventFilter

    var body: some View {
        HStack(spacing: StarpathTokens.spacingSM) {
            ForEach(EventFilter.allCases, id: \.self) { filter in
                Button {
                    selected = filter
                } label: {
                    Text(filter.rawValue)
                        .starpathSans()
                        .foregroundStyle(
                            filter == selected
                                ? StarpathTokens.parchment
                                : StarpathTokens.obsidian
                        )
                        .padding(.horizontal, StarpathTokens.spacingMD)
                        .padding(.vertical, StarpathTokens.spacingSM)
                        .background(
                            filter == selected
                                ? StarpathTokens.obsidian
                                : Color.clear
                        )
                        .clipShape(Capsule())
                        .overlay {
                            if filter != selected {
                                Capsule()
                                    .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                            }
                        }
                }
            }
            Spacer()
        }
    }
}
