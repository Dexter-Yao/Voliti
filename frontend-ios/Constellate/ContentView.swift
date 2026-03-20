// ABOUTME: 应用根视图，TabView 承载三个页签
// ABOUTME: Coach / Map / Journal 全部就位

import SwiftUI
import SwiftData

struct ContentView: View {
    var body: some View {
        TabView {
            CoachView()
                .tabItem {
                    Label("COACH", systemImage: "message")
                }

            MapView()
                .tabItem {
                    Label("MAP", systemImage: "map")
                }

            JournalView()
                .tabItem {
                    Label("JOURNAL", systemImage: "book")
                }
        }
        .tint(StarpathTokens.obsidian)
    }
}

#Preview {
    ContentView()
        .modelContainer(for: [
            ChatMessage.self,
            BehaviorEvent.self,
            InterventionCard.self,
            Chapter.self,
        ], inMemory: true)
}
