import XCTest
final class TapTests: XCTestCase {
 func testWebKitTouches() throws {
  let safari = XCUIApplication(bundleIdentifier: "local.psycho.TrainerTestHost")
  safari.launch()
  let deadline=Date().addingTimeInterval(600)
  while Date()<deadline {
   let semaphore=DispatchSemaphore(value:0)
   var command:[String:Any]?
   URLSession.shared.dataTask(with:URL(string:"http://127.0.0.1:5151/next")!){data,_,_ in
    if let data=data {command=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any]}
    semaphore.signal()
   }.resume()
   if semaphore.wait(timeout:.now()+3) == .timedOut {continue}
   guard let c=command else {Thread.sleep(forTimeInterval:0.2);continue}
   if c["stop"] as? Bool == true {break}
   if let x=c["x"] as? Double,let y=c["y"] as? Double {
    let web=safari.webViews.firstMatch
    if web.waitForExistence(timeout:5) {
     web.coordinate(withNormalizedOffset:CGVector(dx:0,dy:0)).withOffset(CGVector(dx:x,dy:y)).tap()
    }
    URLSession.shared.dataTask(with:URL(string:"http://127.0.0.1:5151/done")!).resume()
   }
  }
 }
}
