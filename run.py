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

    with open('friends.txt') as f:
        friends = [s.strip() for s in f.readlines()]

    with open('last_following.txt') as f:
        last_following = [s.strip() for s in f.readlines()]

    session = InstaPy(
        username=config['username'],
        password=config['password'],
        headless_browser=True,
        show_logs=not silent,
        disable_image_load=True,
        multi_logs=False,
    )

    try:
        session.login()

        current_following = session.grab_following(username=session.username, amount="full")
        new_friends = [x for x in current_following if (x not in last_following and x not in friends)]
        if len(new_friends)>0:
            friends.extend(new_friends)
            with open('friends.txt', 'w') as f:
                f.writelines(map(lambda s: s + '\n', friends))

        ##########
        # settings

        #session.set_relationship_bounds(
        #    enabled=True,
        #    potency_ratio=-0.9,
        #    delimit_by_numbers=True,
        #    max_followers=2000,
        #    max_following=1000,
        #    min_followers=5,
        #    min_following=10,
        #)

        session.set_delimit_liking(enabled=True, max=242, min=24)

        session.set_dont_include(friends)

        session.set_quota_supervisor(enabled=True,
                                     sleep_after=['follows', 'server_calls_h'],
                                     sleepyhead=True, stochastic_flow=True,
                                     peak_likes=(50, 600),
                                     peak_comments=(20, 250),
                                     peak_follows=(40, 400),
                                     peak_unfollows=(30, 500),
                                     peak_server_calls=(None, 4700)
                                     )

        session.set_dont_like(config['ignore_tags'])

        ##########
        # do stuff

        # update the follower graph
        try:
            subprocess.call(["./plot_followers.R"], stderr=subprocess.DEVNULL)
        except Exception as e:
            print('warning: graph not updated')
            print(e)

        if 'like_by_tag' in config:
            session.like_by_tags(config['like_by_tag']['tags'], amount=config['like_by_tag']['amount'])


        #session.unfollow_users(
        #    amount=100,
        #    allFollowing=True,
        #    unfollow_after=1.5*24*60*60,
        #    sleep_delay=655,
        #)


        #########
        # save people currently followed
        following = session.grab_following(username=session.username, amount="full")
        with open('last_following.txt', 'w') as f:
            f.writelines(map(lambda s: s + '\n', following))

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
