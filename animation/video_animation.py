import cv2
import numpy as np
import logging
import time
import os

logger = logging.getLogger(__name__)

class VideoAnimation:
    def __init__(self, video_paths: dict):
        logger.info("Initializing VideoAnimation")
        self.states = {
            "waiting": {"video": None, "enabled": False},
            "listening": {"video": None, "enabled": False},
            "speaking": {"video": None, "enabled": False},
            "thinking": {"video": None, "enabled": False}
        }
        
        # Load all videos
        for state, video_path in video_paths.items():
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            self.states[state]["video"] = cap
            logger.info(f"Loaded video for state {state}: {video_path}")
        
        # Get video properties from waiting state video
        waiting_video = self.states["waiting"]["video"]
        self.frame_count = int(waiting_video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = waiting_video.get(cv2.CAP_PROP_FPS)
        self.frame_time = 1.0 / self.fps
        self.next_frame_time = 0
        
        self.window_name = "AI Assistant"
        self.running = False
        self.current_state = "waiting"
        logger.info("VideoAnimation initialization complete")

    def start(self):
        logger.info("Starting VideoAnimation")
        self.running = True
        self.next_frame_time = time.time()
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1024, 1024)
        self.set_state("waiting", True)

    def update(self):
        if not self.running:
            return False
            
        try:
            current_time = time.time()
            
            if current_time >= self.next_frame_time:
                # Get current active video
                active_video = self.states[self.current_state]["video"]
                ret, frame = active_video.read()
                
                # Reset video to start if we've reached the end
                if not ret:
                    logger.debug(f"Resetting {self.current_state} video to start")
                    active_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = active_video.read()
                
                if ret:
                    cv2.imshow(self.window_name, frame)
                    self.next_frame_time = current_time + self.frame_time
                else:
                    logger.error(f"Failed to read frame from {self.current_state} video")
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                logger.info("ESC key pressed - stopping animation")
                self.running = False
                return False
                
        except Exception as e:
            logger.error(f"Error in animation update: {e}", exc_info=True)
            self.running = False
            return False
            
        return True

    def set_state(self, state_name: str, value: bool):
        """
        Set the state of a specific animation layer.
        Each state is managed independently without affecting others.
        
        Args:
            state_name (str): Name of the state to modify
            value (bool): New value for the state
        """
        if state_name not in self.states:
            logger.warning(f"Unknown state: {state_name}")
            return
        
        logger.debug(f"Before state change - Current states: {[(s, self.states[s]['enabled']) for s in self.states]}")
        
        if value:
            # Enabling a state: disable all others first
            for state in self.states:
                self.states[state]["enabled"] = False
            self.states[state_name]["enabled"] = True
            self.current_state = state_name
            logger.info(f"Switched to state: {state_name}")
        else:
            # Disabling a state: only switch to waiting if no other states are active
            self.states[state_name]["enabled"] = False
            # Add a small delay before checking if we should switch to waiting
            time.sleep(0.1)  # 100ms delay
            any_active = any(self.states[s]["enabled"] for s in self.states if s != "waiting")
            if not any_active:
                self.states["waiting"]["enabled"] = True
                self.current_state = "waiting"
                logger.info("Switched back to waiting state")
        
        logger.debug(f"After state change - Current states: {[(s, self.states[s]['enabled']) for s in self.states]}")

    def stop(self):
        logger.info("Stopping VideoAnimation")
        self.running = False
        for state in self.states.values():
            if state["video"] and state["video"].isOpened():
                state["video"].release()
        cv2.destroyAllWindows()
        logger.info("VideoAnimation cleanup complete")