import UIKit
import WebKit
@main class App: UIResponder, UIApplicationDelegate {
 var window:UIWindow?
 func application(_ application:UIApplication,didFinishLaunchingWithOptions launchOptions:[UIApplication.LaunchOptionsKey:Any]?)->Bool {
  let w=UIWindow(frame:UIScreen.main.bounds);w.rootViewController=Browser();w.makeKeyAndVisible();window=w;return true
 }
}
class Browser:UIViewController {
 let web=WKWebView(frame:.zero);var timer:Timer?
 override func viewDidLoad(){super.viewDidLoad();view.backgroundColor = .white;web.translatesAutoresizingMaskIntoConstraints=false;view.addSubview(web);NSLayoutConstraint.activate([web.leadingAnchor.constraint(equalTo:view.leadingAnchor),web.trailingAnchor.constraint(equalTo:view.trailingAnchor),web.topAnchor.constraint(equalTo:view.safeAreaLayoutGuide.topAnchor),web.bottomAnchor.constraint(equalTo:view.safeAreaLayoutGuide.bottomAnchor)]);web.load(URLRequest(url:URL(string:"http://127.0.0.1:8787/")!));timer=Timer.scheduledTimer(withTimeInterval:0.15,repeats:true){_ in self.poll()}}
 var busy=false
 func send(_ value:Any){let body=(try? JSONSerialization.data(withJSONObject:["value":value],options:[.fragmentsAllowed])) ?? Data("{\"value\":null}".utf8);var r=URLRequest(url:URL(string:"http://127.0.0.1:5151/result")!);r.httpMethod="POST";r.httpBody=body;r.setValue("application/json",forHTTPHeaderField:"Content-Type");URLSession.shared.dataTask(with:r){_,_,_ in DispatchQueue.main.async{self.busy=false}}.resume()}
 func poll(){if busy{return};busy=true;URLSession.shared.dataTask(with:URL(string:"http://127.0.0.1:5151/script")!){data,_,error in
  guard let data=data,let c=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any],let code=c["script"] as? String else{DispatchQueue.main.async{self.busy=false};return}
  DispatchQueue.main.async{
   if code=="__screenshot__"{self.web.takeSnapshot(with:nil){image,error in self.send(image?.pngData()?.base64EncodedString() ?? "")}}
   else{self.web.evaluateJavaScript(code){value,error in self.send(error == nil ? (value ?? NSNull()) : ["error":error!.localizedDescription])}}
  }
 }.resume()}
}
