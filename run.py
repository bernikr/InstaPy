import getopt
import json
import os
import subprocess
import sys
import time
from tempfile import gettempdir

from selenium.common.exceptions import NoSuchElementException

from instapy import InstaPy

# set headless_browser=True if you want to run InstaPy on a server

# set these in instapy/settings.py if you're locating the
# library in the /usr/lib/pythonX.X/ directory:
#   Settings.database_location = '/path/to/instapy.db'
#   Settings.chromedriver_location = '/path/to/chromedriver'


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "s")
    except getopt.GetoptError:
        print('run.py [-s]')
        sys.exit(2)

    silent = False
    for opt, arg in opts:
        if opt == '-s':
            silent = True

    with open('config.json') as f:
        config = json.load(f)

    session = InstaPy(
        username=config['username'],
        password=config['password'],
        headless_browser=True,
        show_logs=not silent,
        multi_logs=True,
        disable_image_load=True,
    )

    try:
        session.login()

        ##########
        # settings

        session.set_relationship_bounds(
            enabled=True,
            potency_ratio=-0.9,
            delimit_by_numbers=True,
            max_followers=2000,
            max_following=1000,
            min_followers=5,
            min_following=10,
        )

        session.set_dont_include(config['dont_unfollow'])

        session.set_do_like(
            enabled=True,
            percentage=30,
        )

        session.set_user_interact(
            amount=5,
            randomize=False,
        )

        ##########
        # do stuff

        # update the follower graph
        try:
            subprocess.call(["./plot_followers.R", session.username], stderr=subprocess.DEVNULL)
        except Exception as e:
            print('warning: graph not updated')
            print(e)

        session.follow_user_followers(
            config['rolemodels'],
            amount=20,
            randomize=True,
            interact=True,
        )

        session.set_dont_unfollow_active_users(enabled=True, posts=5)
        session.unfollow_users(
            amount=100,
            #nonFollowers=True,
            allFollowing=True,
            unfollow_after=3*24*60*60,
            sleep_delay=655,
        )

    except Exception as exc:
        # if changes to IG layout, upload the file to help us locate the change
        if isinstance(exc, NoSuchElementException):
            file_path = os.path.join(gettempdir(), '{}.html'.format(time.strftime('%Y%m%d-%H%M%S')))
            with open(file_path, 'wb') as fp:
                fp.write(session.browser.page_source.encode('utf8'))
            print('{0}\nIf raising an issue, please also upload the file located at:\n{1}\n{0}'.format(
                '*' * 70, file_path))
        # full stacktrace when raising Github issue
        raise

    finally:
        # end the bot session
        session.end()


if __name__ == "__main__":
    main(sys.argv[1:])
