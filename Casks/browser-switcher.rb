cask "browser-switcher" do
  version "0.2.0"
  sha256 "40a2a70dde5544828da1a9eedbef088811479dca1c0d50b315615b8bd57c7cc2"

  url "https://github.com/cjustice/browser-switcher/releases/download/v#{version}/BrowserSwitcher-#{version}.zip"
  name "Browser Switcher"
  desc "Drives Finicky to switch the default browser on a weekday schedule"
  homepage "https://github.com/cjustice/browser-switcher"

  depends_on macos: ">= :ventura"
  depends_on cask: "finicky"

  app "Browser Switcher.app"

  postflight do
    # Strip Gatekeeper quarantine xattr so the ad-hoc-signed app launches
    # without prompting. Remove this once the app is properly notarized.
    system_command "/usr/bin/xattr",
                   args: ["-dr", "com.apple.quarantine", "#{appdir}/Browser Switcher.app"]
  end

  zap trash: [
    "~/Library/Preferences/com.connorjustice.BrowserSwitcher.plist",
  ]
end
