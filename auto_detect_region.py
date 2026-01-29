import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class SubtitleRegionDetector:
    """
    Automatically detect subtitle region by analyzing frame differences.
    Uses multi-threading for faster processing.
    """
    
    def __init__(self, video_path, sample_frames=30, num_threads=4):
        """
        Args:
            video_path: Path to video file
            sample_frames: Number of frames to sample for analysis
            num_threads: Number of threads for parallel processing
        """
        self.video_path = video_path
        self.sample_frames = sample_frames
        self.num_threads = num_threads
        
    def detect_subtitle_region(self, progress_callback=None):
        """
        Detect the region where subtitles appear by analyzing frame differences.
        Returns: (ymin, ymax, xmin, xmax) as percentages (0.0 to 1.0)
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        # Sample frames evenly throughout the video
        frame_indices = np.linspace(0, total_frames - 1, self.sample_frames, dtype=int)
        
        # Read frames in parallel
        frames = []
        
        def read_frame(idx):
            cap_local = cv2.VideoCapture(self.video_path)
            cap_local.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap_local.read()
            cap_local.release()
            if ret:
                # Convert to grayscale for difference analysis
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                return idx, gray
            return idx, None
        
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(read_frame, idx) for idx in frame_indices]
            
            for i, future in enumerate(as_completed(futures)):
                idx, frame = future.result()
                if frame is not None:
                    frames.append((idx, frame))
                if progress_callback:
                    progress_callback(i / len(futures) * 0.5)  # First 50% is reading
        
        # Sort by frame index
        frames.sort(key=lambda x: x[0])
        frames = [f[1] for f in frames]
        
        if len(frames) < 2:
            # Fallback to default bottom 25%
            return (0.75, 1.0, 0.0, 1.0)
        
        # Calculate difference maps between consecutive frames
        diff_maps = []
        
        def calc_diff(i):
            if i >= len(frames) - 1:
                return None
            diff = cv2.absdiff(frames[i], frames[i + 1])
            # Apply threshold to get binary difference
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            return thresh
        
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(calc_diff, i) for i in range(len(frames) - 1)]
            
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                if result is not None:
                    diff_maps.append(result)
                if progress_callback:
                    progress_callback(0.5 + (i / len(futures) * 0.3))  # 50-80%
        
        if not diff_maps:
            return (0.75, 1.0, 0.0, 1.0)
        
        # Accumulate all differences to find regions with most change
        accumulated_diff = np.zeros((height, width), dtype=np.float32)
        for diff in diff_maps:
            accumulated_diff += diff.astype(np.float32)
        
        # Normalize
        accumulated_diff = accumulated_diff / len(diff_maps)
        
        # Find horizontal bands (rows) with high activity
        row_activity = np.sum(accumulated_diff, axis=1)
        
        # Find the region with consistent activity (likely subtitle area)
        # Subtitles usually appear in bottom 50% of screen
        search_start = int(height * 0.5)
        row_activity_bottom = row_activity[search_start:]
        
        # Smooth the signal
        from scipy.ndimage import gaussian_filter1d
        smoothed = gaussian_filter1d(row_activity_bottom, sigma=5)
        
        # Find peaks (areas with high change)
        threshold = np.percentile(smoothed, 70)  # Top 30% activity
        active_rows = np.where(smoothed > threshold)[0]
        
        if len(active_rows) > 0:
            # Find continuous region
            # Get the largest continuous block
            gaps = np.diff(active_rows)
            gap_threshold = 10  # Allow small gaps
            
            # Split into groups
            groups = []
            current_group = [active_rows[0]]
            
            for i in range(1, len(active_rows)):
                if gaps[i-1] <= gap_threshold:
                    current_group.append(active_rows[i])
                else:
                    groups.append(current_group)
                    current_group = [active_rows[i]]
            groups.append(current_group)
            
            # Find largest group
            largest_group = max(groups, key=len)
            
            # Convert back to full frame coordinates
            y_start = search_start + min(largest_group)
            y_end = search_start + max(largest_group)
            
            # Add some padding
            padding = int(height * 0.05)
            y_start = max(0, y_start - padding)
            y_end = min(height, y_end + padding)
            
            # For horizontal, analyze column activity in the detected vertical region
            col_activity = np.sum(accumulated_diff[y_start:y_end, :], axis=0)
            smoothed_col = gaussian_filter1d(col_activity, sigma=10)
            
            col_threshold = np.percentile(smoothed_col, 30)  # Keep most of width
            active_cols = np.where(smoothed_col > col_threshold)[0]
            
            if len(active_cols) > 0:
                x_start = max(0, min(active_cols) - int(width * 0.05))
                x_end = min(width, max(active_cols) + int(width * 0.05))
            else:
                x_start = 0
                x_end = width
            
            # Convert to percentages
            ymin = y_start / height
            ymax = y_end / height
            xmin = x_start / width
            xmax = x_end / width
            
            if progress_callback:
                progress_callback(1.0)
            
            cap.release()
            return (ymin, ymax, xmin, xmax)
        
        # Fallback
        if progress_callback:
            progress_callback(1.0)
        cap.release()
        return (0.75, 1.0, 0.0, 1.0)


def auto_detect_subtitle_region(video_path, progress_callback=None):
    """
    Convenience function to auto-detect subtitle region.
    """
    try:
        detector = SubtitleRegionDetector(video_path, sample_frames=30, num_threads=4)
        region = detector.detect_subtitle_region(progress_callback)
        return region
    except Exception as e:
        print(f"Auto-detection failed: {e}")
        return (0.75, 1.0, 0.0, 1.0)  # Default fallback
