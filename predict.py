import os
import tempfile
import subprocess
import time
import shutil
from pathlib import Path as PathLib
from cog import BasePredictor, Path, Input

class Predictor(BasePredictor):
    def setup(self):
        """Prepare environment."""
        print("Working directory:", os.getcwd())
        print("Setting up FaceFusion for video processing...")
    
    def predict(
        self,
        source: Path = Input(description="Source face image to use for swapping"),
        target: Path = Input(description="Target video to apply face swap to"),
        reference_face_position: int = Input(
            description="Default face position in source (0 = first face)",
            default=0,
            ge=0,
            le=10
        ),
        output_video_quality: int = Input(
            description="Output video quality (1-100)",
            default=80,
            ge=1,
            le=100
        ),
        output_video_fps: int = Input(
            description="Output video framerate",
            default=25,
            ge=1,
            le=60
        ),
        processors: str = Input(
            description="Processors to use",
            default="face_swapper,face_enhancer",
            choices=["face_swapper", "face_swapper,face_enhancer"]
        )
    ) -> Path:
        """Run face swap with FaceFusion using trim-based processing."""
        # Validate inputs
        if not os.path.exists(source):
            raise ValueError(f"Source file not found: {source}")
        if not os.path.isfile(source):
            raise ValueError(f"Source is not a file: {source}")
            
        if not os.path.exists(target):
            raise ValueError(f"Target file not found: {target}")
        if not os.path.isfile(target):
            raise ValueError(f"Target is not a file: {target}")
            
        # Check for file types
        source_ext = os.path.splitext(str(source))[1].lower()
        if source_ext in ['.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv']:
            raise ValueError("Source must be an image file, not a video")
        
        # Determine if target is image or video
        target_extension = os.path.splitext(str(target))[1].lower()
        is_video = target_extension in ['.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv']
        if not is_video:
            raise ValueError("Target must be a video file for multi-frame processing")
        
        # Define the specific frame ranges and settings for each iteration
        iterations_config = [
            {
                "trim_frame_start": 0,
                "trim_frame_end": 61,
                "reference_frame_number": 19,
                "reference_face_position": 1,  # Override: use position 1 for this segment
                "face_mask_types": ["occlusion", "region"],
                "face_mask_padding": None,
                "reference_face_distance": 0.65,
                "skip_audio": True    # Default value
            },
            {
                "trim_frame_start": 62,
                "trim_frame_end": 105,
                "reference_frame_number": 100,
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region", "box"],
                "face_mask_padding": [45, 0, 23, 22],
                "reference_face_distance": 0.65,
                "skip_audio": True
            },
            {
                "trim_frame_start": 106,
                "trim_frame_end": 147,
                "reference_frame_number": 106,  # Using start frame as reference
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region", "box"],
                "face_mask_padding": [52, 0, 23, 22],
                "reference_face_distance": 0.65,
                "skip_audio": True
            },
            {
                "trim_frame_start": 148,
                "trim_frame_end": 241,
                "reference_frame_number": 198,
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region", "box"],
                "face_mask_padding": [52, 0, 0, 22],
                "reference_face_distance": 0.65,
                "skip_audio": True
            },
            {
                "trim_frame_start": 242,
                "trim_frame_end": 565,
                "reference_frame_number": 479,
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region"],
                "face_mask_padding": None,
                "reference_face_distance": 0.65,
                "skip_audio": True
            },
            {
                "trim_frame_start": 583,
                "trim_frame_end": 625,
                "reference_frame_number": 605,  # Using start frame as reference
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region", "box"],
                "face_mask_padding": [45, 0, 0, 0],  # Single value expanded to all sides
                "reference_face_distance": 0.8,
                "skip_audio": True
            }
        ]
        
        # Get video info
        video_info = self._get_video_info(str(target))
        video_fps = video_info['fps']
        video_duration = video_info['duration']
        video_frame_count = video_info['frame_count']
        
        # Identify non-processed frame ranges (passing the total frame count)
        non_processed_ranges = self._find_non_processed_ranges(iterations_config, video_frame_count)
        
        print(f"Video info: {video_frame_count} frames, {video_fps} fps, {video_duration} seconds")
        print(f"Processing {len(iterations_config)} segments with frame ranges:")
        for i, config in enumerate(iterations_config):
            print(f"  Segment {i+1}: Process frames {config['trim_frame_start']} to {config['trim_frame_end']} (Ref frame: {config['reference_frame_number']}, Ref pos: {config['reference_face_position']})")
        
        print(f"Non-processed ranges: {len(non_processed_ranges)}")
        for i, range_info in enumerate(non_processed_ranges):
            print(f"  Range {i+1}: Frames {range_info['start']} to {range_info['end']}")
        
        # Generate output filename for final result
        source_name = os.path.splitext(os.path.basename(str(source)))[0]
        target_name = os.path.splitext(os.path.basename(str(target)))[0]
        timestamp = int(time.time())
        output_filename = f"{source_name}_on_{target_name}_{timestamp}.mp4"
        final_output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
        # Create a temporary directory for intermediate files
        temp_dir = os.path.join(tempfile.gettempdir(), f"facefusion_temp_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Try to find facefusion.py
        facefusion_script = None
        for possible_path in ["facefusion.py", "/src/facefusion.py"]:
            if os.path.exists(possible_path):
                facefusion_script = possible_path
                print(f"Found FaceFusion script at: {facefusion_script}")
                break
        
        if not facefusion_script:
            raise RuntimeError("Could not find facefusion.py script!")
        
        # Extract Audio Once from the Original Target Video
        audio_temp_path = os.path.join(tempfile.gettempdir(), f"temp_audio_{timestamp}.aac")
        print("Extracting audio from original target video...")
        cmd_audio = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(target),
            "-vn", "-c:a", "copy",  # Using copy mode to preserve audio quality
            "-y", audio_temp_path
        ]
        subprocess.run(cmd_audio, check=True)
        print(f"Audio extracted to: {audio_temp_path}")
        
        # List to track all segments in order
        all_segments = []
        
        # Process each specified segment with FaceFusion
        for i, config in enumerate(iterations_config):
            segment_number = i + 1
            trim_frame_start = config["trim_frame_start"]
            trim_frame_end = config["trim_frame_end"]
            reference_frame_number = config["reference_frame_number"]
            ref_face_pos = config["reference_face_position"]
            face_mask_types = config["face_mask_types"]
            face_mask_padding = config["face_mask_padding"]
            reference_face_distance = config["reference_face_distance"]
            skip_audio = config["skip_audio"]
            
            # Define output path for this segment
            segment_output = os.path.join(temp_dir, f"segment_{segment_number}.mp4")
            
            print(f"\nProcessing segment {segment_number}/{len(iterations_config)}: Frames {trim_frame_start} to {trim_frame_end}...")
            
            # Build command for processing this segment
            cmd = [
                "python", facefusion_script, "headless-run",
                "-s", str(source),
                "-t", str(target),  # Always use original video
                "-o", segment_output,
                "--face-detector-model", "yoloface",
                "--face-detector-size", "640x640",
                "--face-detector-angles", "0", "90",
                "--face-landmarker-model", "2dfan4",
                "--face-landmarker-score", "0.5",
                "--face-selector-mode", "reference",
                "--face-selector-order", "large-small",
                "--reference-face-position", str(ref_face_pos),
                "--reference-face-distance", str(reference_face_distance),
                "--reference-frame-number", str(reference_frame_number),
                "--face-occluder-model", "xseg_1",
                "--face-parser-model", "bisenet_resnet_34",
                "--temp-frame-format", "png",
                "--output-image-quality", "80",
                "--output-image-resolution", "1920x1080",
                "--output-audio-encoder", "aac",
                "--output-video-encoder", "libx264",
                "--output-video-preset", "veryfast",  # Using your original preset
                "--output-video-quality", str(output_video_quality),
                "--output-video-resolution", "1080x720",
                "--output-video-fps", str(output_video_fps),
                # Use trim parameters directly
                "--trim-frame-start", str(trim_frame_start),
                "--trim-frame-end", str(trim_frame_end),
                "--face-mask-types"
            ]
            
            cmd.extend(face_mask_types)
            
            # Add skip audio flag
            cmd.append("--skip-audio")
            
            if face_mask_padding:
                cmd.append("--face-mask-padding")
                if isinstance(face_mask_padding, list):
                    cmd.extend([str(p) for p in face_mask_padding])
                else:
                    cmd.append(str(face_mask_padding))
            
            cmd.append("--processors")
            cmd.extend(processors.split(','))
            
            cmd.extend([
                "--face-enhancer-model", "gfpgan_1.4",
                "--face-swapper-model", "inswapper_128",
                "--execution-providers", "cuda",
                "--execution-thread-count", "4",
                "--execution-queue-count", "1",
                "--log-level", "debug"
            ])
            
            print(f"Running FaceFusion with command: {' '.join(cmd)}")
            
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                from threading import Thread
                import queue
                stdout_queue = queue.Queue()
                stderr_queue = queue.Queue()
                
                def read_stdout():
                    for line in iter(process.stdout.readline, ""):
                        if "%" in line:
                            print(f"\r[Segment {segment_number}] Processing: {line.strip()}", end="")
                        else:
                            print(line.strip())
                        stdout_queue.put(line)
                    process.stdout.close()
                
                def read_stderr():
                    for line in iter(process.stderr.readline, ""):
                        print(f"ERROR: {line.strip()}")
                        stderr_queue.put(line)
                    process.stderr.close()
                
                stdout_thread = Thread(target=read_stdout, daemon=True)
                stderr_thread = Thread(target=read_stderr, daemon=True)
                stdout_thread.start()
                stderr_thread.start()
                
                return_code = process.wait()
                print("")
                
                if return_code != 0:
                    stderr_output = ""
                    try:
                        while not stderr_queue.empty():
                            stderr_output += stderr_queue.get_nowait()
                    except queue.Empty:
                        pass
                    
                    if "CUDA out of memory" in stderr_output:
                        raise RuntimeError("GPU ran out of memory. Try processing a smaller video or reducing resolution.")
                    elif "No face detected" in stderr_output:
                        raise ValueError("No faces could be detected in the source image. Please try another image.")
                    else:
                        raise RuntimeError(f"FaceFusion failed with error code {return_code}: {stderr_output}")
                
                if os.path.exists(segment_output) and os.path.getsize(segment_output) > 0:
                    print(f"Successfully processed segment {segment_number}")
                    all_segments.append({
                        "path": segment_output,
                        "start_frame": trim_frame_start,
                        "end_frame": trim_frame_end
                    })
                else:
                    raise RuntimeError(f"Output file not created or empty: {segment_output}")
                
            except Exception as e:
                print(f"Error processing segment {segment_number}: {str(e)}")
                print("Continuing with other segments...")
                continue
        
        # Extract non-processed segments from the original video
        for i, range_info in enumerate(non_processed_ranges):
            start_frame = range_info["start"]
            end_frame = range_info["end"]
            
            # Calculate time values for this segment
            start_time = start_frame / video_fps
            end_time = (end_frame + 1) / video_fps  # +1 to include the end frame
            
            # Define output path for this segment
            non_processed_output = os.path.join(temp_dir, f"non_processed_{i+1}.mp4")
            
            # Extract this segment with high quality encoding
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-i", str(target),
                "-ss", str(start_time),
                "-to", str(end_time),
                "-c:v", "libx264", 
                "-crf", "17",  # Very high quality (lower is better, 0 is lossless)
                "-preset", "veryslow",  # Highest quality preset
                "-force_key_frames", f"expr:gte(t,{start_time})",  # Force keyframe at segment start
                "-an",  # No audio needed
                "-y", non_processed_output
            ]
            
            print(f"Extracting non-processed segment {i+1} (frames {start_frame}-{end_frame}) with high quality...")
            result = subprocess.run(cmd)
            
            if result.returncode == 0 and os.path.exists(non_processed_output) and os.path.getsize(non_processed_output) > 0:
                print(f"Successfully extracted non-processed segment {i+1}")
                all_segments.append({
                    "path": non_processed_output,
                    "start_frame": start_frame,
                    "end_frame": end_frame
                })
            else:
                print(f"Warning: Failed to extract non-processed segment {i+1}")
        
        # Sort all segments by start frame
        all_segments.sort(key=lambda x: x["start_frame"])
        
        # Create a file list for concatenation
        concat_list_path = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_list_path, "w") as f:
            for segment in all_segments:
                f.write(f"file '{segment['path']}'\n")
        
        # Concatenate all segments
        concat_output = os.path.join(temp_dir, "concat_output.mp4")
        concat_cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",  # Use copy mode for the initial concatenation
            "-y", concat_output
        ]
        
        print("Concatenating all segments...")
        concat_result = subprocess.run(concat_cmd)
        
        if concat_result.returncode != 0 or not os.path.exists(concat_output) or os.path.getsize(concat_output) == 0:
            raise RuntimeError("Failed to concatenate video segments")
        
        # Add a final re-encoding step to ensure maximum compatibility
        final_encoded_path = os.path.join(temp_dir, "final_encoded.mp4")
        final_encode_cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", concat_output,
            "-c:v", "libx264", 
            "-crf", "18",  # High quality
            "-preset", "medium",  # Good balance of speed and quality
            "-y", final_encoded_path
        ]
        print("Performing final encoding for maximum compatibility...")
        subprocess.run(final_encode_cmd, check=True)
        
        # Add audio to the final video using the re-encoded version
        final_video_with_audio = final_output_path
        print("Merging extracted audio with the final video...")
        cmd_merge_audio = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", final_encoded_path,
            "-i", audio_temp_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-y", final_video_with_audio
        ]
        subprocess.run(cmd_merge_audio, check=True)
        print(f"Audio merged successfully. Final video with audio saved to: {final_video_with_audio}")
        
        # Clean up temporary files
        print("Cleaning up temporary files...")
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not delete temporary directory {temp_dir}: {str(e)}")
            
        try:
            os.unlink(audio_temp_path)
        except Exception as e:
            print(f"Warning: Could not delete temporary audio file {audio_temp_path}: {str(e)}")
        
        return Path(final_output_path)
    
    def _find_non_processed_ranges(self, iterations_config, total_frame_count=None):
        """Find frame ranges that are not processed by any iteration in a more efficient way."""
        if not iterations_config:
            return []
        # Sort the iterations based on frame start
        iterations_config = sorted(iterations_config, key=lambda x: x["trim_frame_start"])
        # Initialize non-processed range tracking
        non_processed_ranges = []
        min_frame = iterations_config[0]["trim_frame_start"]
        max_processed_frame = iterations_config[-1]["trim_frame_end"]
        
        # Start checking for gaps
        last_end = min_frame - 1  # Initial frame before the first processed range
        for config in iterations_config:
            start = config["trim_frame_start"]
            end = config["trim_frame_end"]
            # If there is a gap between the last end frame and the new start frame, it's unprocessed
            if start > last_end + 1:
                non_processed_ranges.append({
                    "start": last_end + 1,
                    "end": start - 1
                })
            last_end = max(last_end, end)  # Update last processed frame
        
        # Add frames after the last processed segment to the video end if total_frame_count is provided
        if total_frame_count and last_end < total_frame_count - 1:
            non_processed_ranges.append({
                "start": last_end + 1,
                "end": total_frame_count - 1
            })
        
        return non_processed_ranges
    
    def _get_video_info(self, video_path):
        """Get video information using FFprobe."""
        # Get frame rate
        fps_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "csv=p=0",
            video_path
        ]
        fps_result = subprocess.run(fps_cmd, stdout=subprocess.PIPE, text=True)
        fps_str = fps_result.stdout.strip()
        if '/' in fps_str:
            num, den = map(int, fps_str.split('/'))
            fps = num / den
        else:
            fps = float(fps_str)
        
        # Get duration
        duration_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            video_path
        ]
        duration_result = subprocess.run(duration_cmd, stdout=subprocess.PIPE, text=True)
        duration = float(duration_result.stdout.strip())
        
        # Calculate frame count
        frame_count_cmd = [
            "ffprobe", "-v", "error",
            "-count_frames",
            "-select_streams", "v:0",
            "-show_entries", "stream=nb_read_frames",
            "-of", "csv=p=0",
            video_path
        ]
        frame_count_result = subprocess.run(frame_count_cmd, stdout=subprocess.PIPE, text=True)
        try:
            frame_count = int(frame_count_result.stdout.strip())
        except ValueError:
            # If count_frames fails, estimate from duration and fps
            frame_count = int(duration * fps)
        
        return {
            "fps": fps,
            "duration": duration,
            "frame_count": frame_count
        }