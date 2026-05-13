cask "browser-switcher" do
  version "0.3.0"
  sha256 "c454aaf419b35686c18ec88b13e2ad14f0dc676d699334ca7f4ff36f489938eb"

  url "https://github.com/cjustice/browser-switcher/releases/download/v#{version}/BrowserSwitcher-#{version}.zip"
  name "Browser Switcher"
  desc "Drives Finicky to switch the default browser on a weekday schedule"
  homepage "https://github.com/cjustice/browser-switcher"

  depends_on macos: ">= :sonoma"
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
