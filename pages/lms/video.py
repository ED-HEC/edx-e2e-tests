import time

from e2e_framework.page_object import PageObject
from ..lms import BASE_URL


class VideoPage(PageObject):
    """
    Video player in the courseware.
    """

    @property
    def name(self):
        return "lms.video"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self):
        """
        Video players aren't associated with a particular URL.
        """
        raise NotImplemented

    def is_browser_on_page(self):
        return self.is_css_present('section.xmodule_VideoModule')

    @property
    def elapsed_time(self):
        """
        Amount of time elapsed since the start of the video, in seconds.
        """
        elapsed, _ = self._video_time()
        return elapsed

    @property
    def duration(self):
        """
        Total duration of the video, in seconds.
        """
        _, duration = self._video_time()
        return duration

    @property
    def is_playing(self):
        """
        Return a boolean indicating whether the video is playing.
        """
        return self.is_css_present('a.video_control') and self.is_css_present('a.video_control.pause')

    def play(self):
        """
        Start playing the video.
        """
        self.css_click('a.video_control.play')

    def pause(self):
        """
        Pause the video.
        """
        self.css_click('a.video_control.pause')

    def _video_time(self):
        """
        Return a tuple `(elapsed_time, duration)`, each in seconds.
        """
        # The full time has the form "0:32 / 3:14"
        all_times = self.css_text('div.vidtime')

        if len(all_times) == 0:
            self.warning('Could not find video time')

        else:
            full_time = all_times[0]

            # Split the time at the " / ", to get ["0:32", "3:14"]
            elapsed_str, duration_str = full_time.split(' / ')

            # Convert each string to seconds
            return (self._parse_time_str(elapsed_str), self._parse_time_str(duration_str))

    def _parse_time_str(self, time_str):
        """
        Parse a string of the form 1:23 into seconds (int).
        """
        time_obj = time.strptime(time_str, '%M:%S')
        return time_obj.tm_min * 60 + time_obj.tm_sec
