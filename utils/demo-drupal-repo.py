from screenshot_archiver import WebsiteScreenshotArchiver
import time

class ScreenShots(WebsiteScreenshotArchiver):
  def browse_site(self):
    self.navigateTo("https://github.com/GovReady/govready-q")
    time.sleep(3)

    for repo in ["demo-drupal-on-docker"]:
      repo_url = "https://github.com/GovReady/"+repo
      self.navigateTo(repo_url)
      self.screenshot(repo+"_cm_git_repo")

      self.navigateTo(repo_url + "/graphs/contributors")
      time.sleep(4) # Allow contributor graph to be displayed
      self.screenshot(repo+"_cm_git_repo_contributors")

      self.navigateTo(repo_url + "/pulls")
      self.screenshot(repo+"cm_git_repo_pull_requests")

# Start up the script when this module is run on the command-line.
if __name__ == "__main__":
  ScreenShots().__main__()
