// ABOUTME: Mirror 日志范围 UI smoke，验证预设范围切换后的日志投影变化
// ABOUTME: 使用启动场景夹具，避免依赖真实网络与持久化历史

import XCTest

final class VolitiUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testMirrorLogRangeSwitchShowsOlderFilter() throws {
        let app = XCUIApplication()
        app.launchEnvironment["VOLITI_UI_TEST_SCENARIO"] = "mirrorLogRange"
        app.launch()

        let mirrorTab = app.buttons["tab.mirror"]
        XCTAssertTrue(mirrorTab.waitForExistence(timeout: 5))
        mirrorTab.tap()

        let rangeButton = app.buttons["mirror.logRangeButton"]
        XCTAssertTrue(rangeButton.waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["mirror.filter.state"].exists)

        rangeButton.tap()
        let last90DaysButton = app.buttons["mirror.logRange.last90Days"]
        XCTAssertTrue(last90DaysButton.waitForExistence(timeout: 5))
        last90DaysButton.tap()

        XCTAssertTrue(app.buttons["mirror.filter.state"].waitForExistence(timeout: 5))
    }
}
