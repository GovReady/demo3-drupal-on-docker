from screenshot_archiver import WebsiteScreenshotArchiver
import time

class Screenshots(WebsiteScreenshotArchiver):
  def browse_site(self):

    self.navigateTo("https://account.thehartford.com/customer/#/login?appid=OBSC&goto=https:%2F%2Fbusiness.thehartford.com%2Fpolicies")
    self.screenshot("insurance-login")
    # Pause for login
    time.sleep( 35 )

    # Policies
    self.navigateTo("https://business.thehartford.com/policies")
    self.screenshot("insurance-policies")

# Start up the script when this module is run on the command-line.
if __name__ == "__main__":
  Screenshots().__main__()
