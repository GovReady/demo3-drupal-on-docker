import logging
import re
from datetime import datetime

try:
  from tempfile import TemporaryDirectory
except ImportError:
  from backports.tempfile import TemporaryDirectory

import selenium.webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from PIL import Image, ImageOps, ImageDraw, ImageFont

# This Javascript script is injected into every page.
mouse_cursor_script = """
// For automated generation of screenshots and videos,
// add a picture of a cursor that follows the mouse cursor.
// Adapted from:
// https://stackoverflow.com/questions/35867776/visualize-show-mouse-cursor-position-in-selenium-2-tests-for-example-phpunit

// Only initialize once.
if (typeof window.selenium_mouse_cursor_follower != "undefined")
  return;
window.selenium_mouse_cursor_follower = 1;

// Initialize a div that has an icon of a mouse cursor in it.
var mouseimg = document.createElement("img");
mouseimg.setAttribute('src', 'data:image/png;base64,'
  + 'iVBORw0KGgoAAAANSUhEUgAAABQAAAAeCAQAAACGG/bgAAAAAmJLR0QA/4ePzL8AAAAJcEhZcwAA'
  + 'HsYAAB7GAZEt8iwAAAAHdElNRQfgAwgMIwdxU/i7AAABZklEQVQ4y43TsU4UURSH8W+XmYwkS2I0'
  + '9CRKpKGhsvIJjG9giQmliHFZlkUIGnEF7KTiCagpsYHWhoTQaiUUxLixYZb5KAAZZhbunu7O/PKf'
  + 'e+fcA+/pqwb4DuximEqXhT4iI8dMpBWEsWsuGYdpZFttiLSSgTvhZ1W/SvfO1CvYdV1kPghV68a3'
  + '0zzUWZH5pBqEui7dnqlFmLoq0gxC1XfGZdoLal2kea8ahLoqKXNAJQBT2yJzwUTVt0bS6ANqy1ga'
  + 'VCEq/oVTtjji4hQVhhnlYBH4WIJV9vlkXLm+10R8oJb79Jl1j9UdazJRGpkrmNkSF9SOz2T71s7M'
  + 'SIfD2lmmfjGSRz3hK8l4w1P+bah/HJLN0sys2JSMZQB+jKo6KSc8vLlLn5ikzF4268Wg2+pPOWW6'
  + 'ONcpr3PrXy9VfS473M/D7H+TLmrqsXtOGctvxvMv2oVNP+Av0uHbzbxyJaywyUjx8TlnPY2YxqkD'
  + 'dAAAAABJRU5ErkJggg==');
mouseimg.setAttribute('id', 'selenium_mouse_follower');
mouseimg.setAttribute('style', 'display: none; position: absolute; z-index: 99999999999; pointer-events: none;');
document.body.appendChild(mouseimg);

// Put the image where we last saw the mouse on a previous page
// so that when navigating from page to page the mouse stays
// where it is instead of being reset to some arbitrary location.
var xy = sessionStorage.getItem("mouse_cursor_follower_mouse_position");
if (xy) {
  xy = xy.split(/,/);
  mouseimg.style.display = "block";
  mouseimg.style.left = xy[0] + "px";
  mouseimg.style.top = xy[1] + "px";
}

// Track the actual mouse. Selenium clicks cause the mouse position
// to move.
window.addEventListener("mousemove", function(e) {
  mouseimg.style.display = "block";
  mouseimg.style.left = e.pageX + "px";
  mouseimg.style.top = e.pageY + "px";
  sessionStorage.setItem("mouse_cursor_follower_mouse_position", e.pageX + "," + (e.pageY-$(window).scrollTop()));
});

// Add a function that lets us position the mouse directly
// onto an element.
window.moveMouseToElem = function(elem) {
  var bounds = elem.getBoundingClientRect();
  mouseimg.style.display = "block";
  mouseimg.style.left = (bounds.left+bounds.width/2) + "px";
  mouseimg.style.top = (bounds.top+bounds.height/2) + "px";
}
"""

class WebsiteScreenshotArchiver(object):
  def __init__(self, options={}):
    # options is a dictionary holding the same set
    # of options that argparse provides when running
    # on the command line.
    self.options = options

  @classmethod
  def __main__(clz):
    # Collect command-line arguments.
    import argparse
    parser = argparse.ArgumentParser(description='Archive a website using Selenium to take a series of screenshots.')
    parser.add_argument('path', help="The path to write screenshots into, either a directory or if saving in PDF format a filename.")
    parser.add_argument('--size', metavar='{width}x{height}', help="The width and height, in pixels, of the headless web browser window, or the value 'maximized' to start the headless browser maximized on whatever desktop it is running on.")
    parser.add_argument('--format', metavar='png,pdf', default="png", help="The output format. Either 'png' or 'pdf'.")
    parser.add_argument('--border', default="1px,black", metavar="1px,black", help="The width and color of a border to put around the image. See https://drafts.csswg.org/css-color-4/#named-colors for color names and https://pillow.readthedocs.io/en/stable/reference/ImageColor.html for other ways to specify colors.")
    options = parser.parse_args()

    # Create an instance of the class this method was called on
    # (it might be a subclass), and run it.
    clz(options).run()
  
  def run(self):
    # Start the headless browser.
    self.start_headless_browser()

    try:
      with TemporaryDirectory() as tempdir:
        if self.options.format in ("png",):
          # When saving images, write to the directory path given
          # in the options.
          self.save_dir = self.options.path
        else:
          # When saving a PDF, save the images first to
          # a temporary directory.
          self.save_dir = tempdir

        # Create an empty list to hold the screenshots we took.
        self.screenshot_image_filenames = []

        # Start browsing.
        self.browse_site()

        if self.options.format == "pdf":
          self.write_pdf()
    finally:
        # Close selenium.
        self.stop_headless_browser()

  # STARTUP/SHUTDOWN UTILITY FUNCTIONS

  def start_headless_browser(self):
      # Initialize Selenium.
      options = selenium.webdriver.ChromeOptions()
      options.add_argument("--incognito")
      options.add_argument("disable-infobars") # "Chrome is being controlled by automated test software."
      if self.options.size == "maximized":
          options.add_argument("start-maximized") # too small screens make clicking some things difficult
      elif self.options.size:
          options.add_argument("--window-size=" + re.sub("[xX]", ",", self.options.size))
      
      self.browser = selenium.webdriver.Chrome(chrome_options=options)
      self.browser.implicitly_wait(3) # seconds to wait when trying to target elements to click (etc.) in case element is not clickable yet during animations and loading and things

  def stop_headless_browser(self):
      self.browser.quit()
      self.browser = None

  def write_pdf(self):
      # Write PDF.
      from fpdf import FPDF
      from PIL import Image
      dpi = 120 # note for calcs below that "pt" units are 1/72th of an inch
      pdf = FPDF(unit="pt")
      for image in self.screenshot_image_filenames:
          # Size the next PDF page to the size of this image.
          with open(image, "rb") as f:
              im = Image.open(f)
              page_size = im.size[0]/dpi*72, im.size[1]/dpi*72
          pdf.add_page(format=page_size)
          pdf.image(image, 0,0, page_size[0], page_size[1])
      pdf.output(self.options.path, "F")
      self.log("Saved {}.".format(self.options.path))

  # MAIN SCRIPT FUNCTION

  def browse_site(self):
    raise TypeError("The browse_site function must be implemented by a subclass.")

  # SCREENSHOTTER

  def log(self, message):
    logging.info(message)

  def screenshot(self, slug):
    # Take a screenshot of the current browser window.
    #
    # `slug` is appended to the filename to give generated image files
    # a descriptive name.

    import os
    import os.path

    # Make the output directory, construct the output filename,
    # and save the screenshot there. Remember the filename for
    # forming a PDF at the end.
    if not os.path.exists(self.save_dir):
      os.makedirs(self.save_dir)
    fn = os.path.join(
        self.save_dir,
        "{:03d}_{}.png".format(len(self.screenshot_image_filenames)+1, slug)
        )
    self.browser.save_screenshot(fn)
    self.screenshot_image_filenames.append(fn)
    self.log("Saved {}.".format(fn))

    # Add a black border to saved images because screenshot
    # backgrounds are close to white and are typically shown
    # on white pages and that doesn't look good.
    # Also add image credit and date stamp for evidence
    m = re.match(r"^(\d+)px,(\w+)", self.options.border)
    if not m:
      raise ValueError("Border option is not valid.")
    border_width = int(m.group(1))
    border_color = m.group(2)
    # Prepare credit text and time stamp
    text = "Captured by Screenshot-Archiver {}".format(datetime.today().strftime('%Y-%m-%d'))
    try:
      font = ImageFont.truetype("arial.ttf", 20)
    except:
      # Maybe you are on a MacOS?
      font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 30)
    im = Image.open(fn)
    # Add credit and timestamp
    draw = ImageDraw.Draw(im)
    # Draw border
    draw.text((im.size[0]/2-60, im.size[1]-60), text, font=font, fill="Black")
    draw.text((im.size[0]/2-60-1, im.size[1]-60-1), text, font=font, fill="Gold")
    ImageOps\
        .expand(im, border=border_width, fill=border_color)\
        .save(fn)

  # BROWSING UTILITY FUNCTIONS

  def navigateTo(self, url):
      self.browser.get(url)

  def click_element(self, css_selector):
    # Move the fake cursor to the location of the element.
    self.move_cursor_to(css_selector)

    # Ensure element is on screen or else it can't be clicked.
    # see https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView
    elem = self.browser.find_element_by_css_selector(css_selector)
    self.browser.execute_script("arguments[0].scrollIntoView({ behavior: 'instant', block: 'nearest', inline: 'nearest' });", elem)

    # Click the element.
    elem.click()

  def fill_field(self, css_selector, text):
    self.browser.find_element_by_css_selector(css_selector).clear()
    self.browser.find_element_by_css_selector(css_selector).send_keys(text)

  def select_option(self, css_selector, value):
    from selenium.webdriver.support.select import Select
    e = self.browser.find_element_by_css_selector(css_selector)
    Select(e).select_by_value(value)

  def move_cursor_to(self, css_selector):
    # Position the fake mouse cursor in the middle of the element
    # identified by the CSS selector in `css_selector`
    self.browser.execute_script(mouse_cursor_script)
    elem = self.browser.find_element_by_css_selector(css_selector)
    self.browser.execute_script("moveMouseToElem(arguments[0]);", elem)
    self.browser.execute_script("arguments[0].scrollIntoView({ behavior: 'instant', block: 'nearest', inline: 'nearest' });", elem)

  def click_with_screenshot(self, css_selector, slug):
    self.move_cursor_to(css_selector)
    self.screenshot(slug)
    self.click_element(css_selector)

