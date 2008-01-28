#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes

from pyglet.app import windows, BaseEventLoop
from pyglet.window.carbon import carbon, types, constants

EventLoopTimerProc = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
kEventDurationForever = ctypes.c_double(constants.kEventDurationForever)

class CarbonEventLoop(BaseEventLoop):
    def run(self):
        self._setup()

        e = ctypes.c_void_p()
        event_dispatcher = carbon.GetEventDispatcherTarget()
        event_loop = carbon.GetMainEventLoop()
        event_queue = carbon.GetMainEventQueue()
        timer = ctypes.c_void_p()
        idle_event_proc = EventLoopTimerProc(self._timer_proc)
        carbon.InstallEventLoopTimer(event_loop,
                                     ctypes.c_double(0.1), #?
                                     kEventDurationForever,
                                     idle_event_proc,
                                     None,
                                     ctypes.byref(timer))

        self._sleep_time = None

        self.dispatch_event('on_enter')

        while not self.has_exit:
            duration = kEventDurationForever
            if self._sleep_time == 0.:
                duration = 0
            if carbon.ReceiveNextEvent(0, None, duration,
                                       True, ctypes.byref(e)) == 0:
                carbon.SendEventToEventTarget(e, event_dispatcher)
                carbon.ReleaseEvent(e)

            # Manual idle event 
            if carbon.GetNumEventsInQueue(event_queue) == 0 or duration == 0:
                self._timer_proc(timer, None)

        self.dispatch_event('on_exit')

    def _timer_proc(self, timer, data):
        for window in windows:
            # Check for live resizing
            if window._resizing is not None:
                old_width, old_height = window._resizing
                rect = types.Rect()
                carbon.GetWindowBounds(window._window, 
                                       constants.kWindowContentRgn,
                                       ctypes.byref(rect))
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                if width != old_width or height != old_height:
                    window._resizing = width, height
                    window.switch_to()
                    window.dispatch_event('on_resize', width, height) 

        self._sleep_time = sleep_time = self.idle()

        if sleep_time is None:
            sleep_time = constants.kEventDurationForever
        carbon.SetEventLoopTimerNextFireTime(timer, ctypes.c_double(sleep_time))
