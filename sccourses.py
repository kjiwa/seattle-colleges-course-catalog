"""A program that extracts Seattle Colleges courses and exports them to CSV.

The Seattle College class schedule is a dynamic web application. A web browser
object is invoked to visit the site and interact with it in order to view and
extract course offerings.
"""

import collections
import csv
import io
import logging
import re
import time

import selenium.common.exceptions
import selenium.webdriver
import titlecase

COURSE_INDICES = {
    'central': 'https://mycentral.seattlecolleges.edu/',
    'north': 'https://mynorth.seattlecolleges.edu/',
    'south': 'https://mysouth.seattlecolleges.edu/'
}


class Course(
    collections.namedtuple('Course', [
        'college', 'department', 'code', 'name', 'credits', 'tags',
        'prerequisites'
    ])):
  """A class representing a course offering."""

  def __eq__(self, other):
    return (self.college == other.college and
            self.department == other.department and self.code == other.code)

  def __hash__(self):
    return hash((self.college, self.department, self.code))


def wait_for_load(browser):
  """Waits for a loading action to complete.

  A page is determined to have completed loading when the "ui-loader" element
  is no longer displayed.

  Args:
    browser: A handle to the browser object.
  """
  loader = browser.find_element_by_class_name('ui-loader')
  while loader.is_displayed():
    time.sleep(0.1)


def parse_tags(course_node):
  """Parses course tags from a course node.

  Args:
    course_node: The node containing course details.

  Returns:
    A list of tags for the course.
  """
  tags = course_node.find_elements_by_class_name('classTags')
  if not tags:
    return []

  tags = tags[0].find_elements_by_tag_name('a')
  return [i.text for i in tags]


def parse_prerequisites(course_node):
  """Parses prerequisites for a course.

  Args:
    course_node: The node containing course details.

  Returns:
    A list of course prerequisites.
  """
  description = course_node.find_element_by_class_name(
      'courseDescription').text
  if 'Prereq:' not in description:
    return []

  p = re.compile(r'(([A-Za-z&]+) *\d+(?!\.))')
  parts = description.split('Coreqs:')[0].split('Prereq:')[1].split('.')

  prerequisites = []
  prev_dept = None
  for i in p.findall(parts[0]):
    if (i[0] in ('a 2', 'with 2', 'of 2', 'least 2', 'minimum 2', 'GPA 2') or
        i[0].startswith('Level ')):
      continue

    if not (i[0].startswith('&') or i[0].startswith('and ') or
            i[0].startswith('or ') or i[0].startswith('into ') or
            i[0].isdigit()):
      m = p.match(i[0])
      prev_dept = m.group(2)
      prerequisites.append(i[0].strip().upper())
      continue

    prerequisites.append(
        '%s%s' %
        (prev_dept,
         i[0].replace('and ', '').replace('into ', '').replace('or ', '')))

  return sorted([i.replace(' ', '') for i in prerequisites])


def parse_course(browser, college, course_node):
  """Parses course information from a node.

  Args:
    browser: A handle to the browser object.
    college: The name of the college from which courses are being extracted.
    course_node: The node containing course details.

  Returns:
    A course object.
  """
  # open the course details
  course_handle = course_node.find_element_by_class_name('course')
  course_handle.click()
  wait_for_load(browser)

  title = course_node.find_element_by_class_name('courseID').text
  m = re.match(r'([A-Z&]+) *(\d+)', title)
  if not m:
    logging.warning('Unable to parse title: %s', title)
    return

  dept = m.group(1)
  code = m.group(2)
  name = titlecase.titlecase(
      course_node.find_element_by_class_name('courseTitle').text)
  creds = float(course_node.find_element_by_class_name('courseCredits').text)
  tags = parse_tags(course_node)
  prerequisites = parse_prerequisites(course_node)

  # close the course details
  course_handle.click()
  wait_for_load(browser)

  return Course(
      titlecase.titlecase(college), dept, code, name, creds, tags,
      prerequisites)


def get_courses(browser, college, dept_node):
  """Gets courses from a department's course description page.

  Args:
    browser: A handle to the web browser.
    college: The name of the college from which courses are being extracted.
    dept_node: The element linking to the department's courses.

  Returns:
    A list of courses offered by the department.
  """
  # enter the department course list
  dept_node.click()
  wait_for_load(browser)

  # parse course entries
  entries = browser.find_element_by_id('courseListHolder')

  courses = []
  for i in entries.find_elements_by_xpath('div/div'):
    course = parse_course(browser, college, i)
    if course:
      courses.append(course)

  # go back to the department index
  back_button = browser.find_element_by_id('btn-deptlist')
  back_button.click()
  wait_for_load(browser)

  return courses


def export_courses(courses, output):
  """Exports courses to CSV.

  Args:
    courses: A list of courses to be exported.
    output: The output buffer to which to write CSV data.
  """
  courses = sorted(courses)
  writer = csv.writer(output)
  writer.writerow([
      'College', 'Department', 'Code', 'Name', 'Credits', 'Tags',
      'Prerequisites'
  ])

  for course in courses:
    writer.writerow([
        course.college, course.department, course.code, course.name,
        course.credits, ','.join(course.tags), ','.join(course.prerequisites)
    ])


def extract_courses(browser, college):
  """Extracts course descriptions.

  Args:
    browser: A handle to the browser object.
    college: The name of the college from which courses are being extracted.

  Returns:
    A list of courses.
  """
  depts = browser.find_element_by_id('departments')
  courses = []
  for i in depts.find_elements_by_tag_name('li'):
    courses += get_courses(browser, college, i)

  return set(courses)


def extract_quarters(browser):
  """Extracts quarters from the course index.

  Args:
    browser: A handle to the browser object.

  Returns:
    A list of available quarters.
  """
  return selenium.webdriver.support.select.Select(
      browser.find_element_by_id('quarterSelector'))


def load_quarter(browser, quarters, option):
  """Activates the course list for the specified quarter.

  Args:
    browser: A handle to the browser object.
    quarters: The quarters select element.
    option: The quarter option to be selected.
  """
  quarters.select_by_value(option.get_attribute('value'))
  wait_for_load(browser)


def create_browser():
  """Creates a web browser object and initializes it.

  Returns:
    A handle to the browser object.
  """
  browser = selenium.webdriver.Chrome()
  return browser


def main():
  """Extracts SSC course descriptions and exports them to CSV."""
  courses = set()
  browser = create_browser()
  for k, v in COURSE_INDICES.items():
    browser.get(v)
    wait_for_load(browser)

    quarters = extract_quarters(browser)
    i = 0
    try:
      while i < len(quarters.options):
        load_quarter(browser, quarters, quarters.options[i])
        courses |= extract_courses(browser, k)
        i += 1
    except selenium.common.exceptions.WebDriverException as e:
      # Every so often the web application fails to load course descriptions,
      # resulting in stale or invisible node references. When these occur,
      # refresh the page and try extracting courses from the quarter again.
      logging.warning(
          'An error occurred extracting courses from %s Seattle College\n%s',
          titlecase.titlecase(k), e)
      quarters = extract_quarters(browser)

  output = io.StringIO()
  export_courses(courses, output)
  print(output.getvalue())
  output.close()

  browser.quit()


main()
