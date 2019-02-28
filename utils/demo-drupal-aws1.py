from screenshot_archiver import WebsiteScreenshotArchiver
import time

class DemoDrupal(WebsiteScreenshotArchiver):
  def browse_site(self):
    self.navigateTo("https://www.amazon.com/ap/signin?openid.assoc_handle=aws&openid.return_to=https%3A%2F%2Fsignin.aws.amazon.com%2Foauth%3Fcoupled_root%3Dtrue%26response_type%3Dcode%26redirect_uri%3Dhttps%253A%252F%252Fconsole.aws.amazon.com%252Fconsole%252Fhome%253Fnc2%253Dh_ct%2526src%253Dheader-signin%2526state%253DhashArgs%252523%2526isauthcode%253Dtrue%26client_id%3Darn%253Aaws%253Aiam%253A%253A015428540659%253Auser%252Fhomepage&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&action=&disableCorpSignUp=&clientContext=&marketPlaceId=&poolName=&authCookies=&pageId=aws.login&siteState=registered%2CEN_US&accountStatusPolicy=P1&sso=&openid.pape.preferred_auth_policies=MultifactorPhysical&openid.pape.max_auth_age=120&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&server=%2Fap%2Fsignin%3Fie%3DUTF8&accountPoolAlias=&forceMobileApp=0&language=EN_US&forceMobileLayout=0&awsEmail=gregelin%40govready.com")
    time.sleep(18)
    self.navigateTo("https://us-east-2.console.aws.amazon.com/ec2/v2/home?region=us-east-2#Instances:sort=instanceId")
    time.sleep(4)
    self.screenshot("aws-instance")
    # Security groups
    self.navigateTo("https://us-east-2.console.aws.amazon.com/ec2/v2/home?region=us-east-2#SecurityGroups:groupId=sg-0897ed9775ba2a5bf;sort=groupId")
    time.sleep(4)
    self.screenshot("aws-security-group-description")
    self.click_element('By.linkText("view inbound rules")')
    time.sleep(4)
    self.screenshot("aws-security-group-inbound")
    
    # self.fill_field("#search_form_input_homepage", "GovReady")
    # self.click_with_screenshot("#search_button_homepage", "search1")

if __name__ == "__main__":
  DemoDrupal().__main__()
