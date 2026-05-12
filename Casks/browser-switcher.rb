cask "browser-switcher" do
  version "0.1.0"
  sha256 "ceacac8d2851f52c86ab24aa3ee7dab46ba6e24b13cce86533b8c8d0cccd48c5"

  url "https://github.com/cjustice/browser-switcher/releases/download/v#{version}/BrowserSwitcher-#{version}.zip"
  name "Browser Switcher"
  desc "Auto-switches default browser between Chrome and Firefox on a schedule"
  homepage "https://github.com/cjustice/browser-switcher"

  depends_on macos: ">= :ventura"

  app "Browser Switcher.app"

  zap trash: [
    "~/Library/Preferences/com.connorjustice.BrowserSwitcher.plist",
  ]
end
