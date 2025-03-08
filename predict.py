# import os
# import tempfile
# import subprocess
# import time
# import shutil
# from pathlib import Path as PathLib
# from cog import BasePredictor, Path, Input

# class Predictor(BasePredictor):
#     def setup(self):
#         """Prepare environment."""
#         print("Working directory:", os.getcwd())
#         print("Setting up FaceFusion for female video processing...")
    
#     def predict(
#         self,
#         source: Path = Input(description="Source face image to use for swapping"),
#         target: Path = Input(description="Target video to apply face swap to"),
#         reference_face_position: int = Input(
#             description="Default face position in source (0 = first face)",
#             default=0,
#             ge=0,
#             le=10
#         ),
#         output_video_quality: int = Input(
#             description="Output video quality (1-100)",
#             default=80,
#             ge=1,
#             le=100
#         ),
#         output_video_fps: int = Input(
#             description="Output video framerate",
#             default=25,
#             ge=1,
#             le=60
#         ),
#         processors: str = Input(
#             description="Processors to use",
#             default="face_swapper,face_enhancer",
#             choices=["face_swapper", "face_swapper,face_enhancer"]
#         )
#     ) -> Path:
#         """Run face swap with FaceFusion using multiple iterations for different frame ranges."""
#         # Validate inputs
#         if not os.path.exists(source):
#             raise ValueError(f"Source file not found: {source}")
#         if not os.path.isfile(source):
#             raise ValueError(f"Source is not a file: {source}")
            
#         if not os.path.exists(target):
#             raise ValueError(f"Target file not found: {target}")
#         if not os.path.isfile(target):
#             raise ValueError(f"Target is not a file: {target}")
            
#         # Check for file types
#         source_ext = os.path.splitext(str(source))[1].lower()
#         if source_ext in ['.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv']:
#             raise ValueError("Source must be an image file, not a video")
        
#         # Determine if target is image or video
#         target_extension = os.path.splitext(str(target))[1].lower()
#         is_video = target_extension in ['.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv']
#         if not is_video:
#             raise ValueError("Target must be a video file for multi-frame processing")
        
#         # Define the specific frame ranges and settings for each iteration,
#         # including a per-iteration reference face position override.
#         iterations_config = [
#             {
#                 "frame_start": 0,
#                 "frame_end": 61,
#                 "reference_frame_number": 19,
#                 "reference_face_position": 1,  # Override: use position 1 for this segment
#                 "face_mask_types": ["occlusion", "region"],
#                 "face_mask_padding": None,
#                 "reference_face_distance": 0.65,
#                 "skip_audio": True    # Default value
#             },
#             {
#                 "frame_start": 62,
#                 "frame_end": 105,
#                 "reference_frame_number": 100,
#                 "reference_face_position": 0,
#                 "face_mask_types": ["occlusion", "region", "box"],
#                 "face_mask_padding": [45, 23, 0, 22],
#                 "reference_face_distance": 0.65,
#                 "skip_audio": True
#             },
#             {
#                 "frame_start": 106,
#                 "frame_end": 147,
#                 "reference_frame_number": 109,  # Using start frame as reference
#                 "reference_face_position": 0,
#                 "face_mask_types": ["occlusion", "region", "box"],
#                 "face_mask_padding": [0, 42, 35, 42],
#                 "reference_face_distance": 0.65,
#                 "skip_audio": True
#             },
#             {
#                 "frame_start": 148,
#                 "frame_end": 241,
#                 "reference_frame_number": 198,
#                 "reference_face_position": 0,
#                 "face_mask_types": ["occlusion", "region", "box"],
#                 "face_mask_padding": [0, 42, 35, 42],
#                 "reference_face_distance": 0.65,
#                 "skip_audio": True
#             },
#             {
#                 "frame_start": 242,
#                 "frame_end": 604,
#                 "reference_frame_number": 479,
#                 "reference_face_position": 0,
#                 "face_mask_types": ["occlusion", "region"],
#                 "face_mask_padding": None,
#                 "reference_face_distance": 0.65,
#                 "skip_audio": True
#             },
#             {
#                 "frame_start": 605,
#                 "frame_end": 625,
#                 "reference_frame_number": 610,  # Using start frame as reference
#                 "reference_face_position": 0,
#                 "face_mask_types": ["occlusion", "region", "box"],
#                 "face_mask_padding": [45, 0, 0, 0],  # Single value expanded to all sides
#                 "reference_face_distance": 0.65,
#                 "skip_audio": False
#             }
#         ]
        
#         iterations = len(iterations_config)
        
#         print(f"Preparing to run {iterations} iterations with frame ranges:")
#         for i, config in enumerate(iterations_config):
#             start = config["frame_start"]
#             end = config["frame_end"]
#             print(f"  Iteration {i+1}: Frames {start} to {end} (Ref frame: {config['reference_frame_number']}, Ref pos: {config['reference_face_position']})")
        
#         # Generate output filename for final result
#         source_name = os.path.splitext(os.path.basename(str(source)))[0]
#         target_name = os.path.splitext(os.path.basename(str(target)))[0]
#         timestamp = int(time.time())
#         output_filename = f"{source_name}_on_{target_name}_{timestamp}.mp4"
#         final_output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
#         # Create a temporary directory for intermediate files
#         temp_dir = os.path.join(tempfile.gettempdir(), f"facefusion_temp_{timestamp}")
#         os.makedirs(temp_dir, exist_ok=True)
        
#         # Try to find facefusion.py
#         facefusion_script = None
#         for possible_path in ["facefusion.py", "/src/facefusion.py"]:
#             if os.path.exists(possible_path):
#                 facefusion_script = possible_path
#                 print(f"Found FaceFusion script at: {facefusion_script}")
#                 break
        
#         if not facefusion_script:
#             raise RuntimeError("Could not find facefusion.py script!")
        
#         # Current target for the first iteration
#         current_target = str(target)
        
#         # Process each iteration
#         for iteration, config in enumerate(iterations_config):
#             iteration_number = iteration + 1
#             frame_start = config["frame_start"]
#             frame_end = config["frame_end"]
#             reference_frame_number = config["reference_frame_number"]
#             ref_face_pos = config["reference_face_position"]
#             face_mask_types = config["face_mask_types"]
#             face_mask_padding = config["face_mask_padding"]
#             reference_face_distance = config["reference_face_distance"]
#             skip_audio = config["skip_audio"]
            
#             print(f"\n[Iteration {iteration_number}/{iterations}] Processing frames {frame_start} to {frame_end}...")
            
#             # Define output for this iteration
#             if iteration == iterations - 1:
#                 iteration_output = final_output_path
#             else:
#                 iteration_output = os.path.join(temp_dir, f"temp_output_iteration_{iteration_number}.mp4")
            
#             # Build command for this iteration
#             cmd = [
#                 "python", facefusion_script, "headless-run",
#                 "-s", str(source),
#                 "-t", current_target,
#                 "-o", iteration_output,
#                 "--face-detector-model", "yoloface",
#                 "--face-detector-size", "640x640",
#                 "--face-detector-angles", "0", "90",
#                 "--face-landmarker-model", "2dfan4",
#                 "--face-landmarker-score", "0.5",
#                 "--face-selector-mode", "reference",
#                 "--face-selector-order", "large-small",
#                 "--reference-face-position", str(ref_face_pos),
#                 "--reference-face-distance", str(reference_face_distance),
#                 "--reference-frame-number", str(reference_frame_number),
#                 "--face-occluder-model", "xseg_1",
#                 "--face-parser-model", "bisenet_resnet_34",
#                 "--temp-frame-format", "png",
#                 "--output-image-quality", "80",
#                 "--output-image-resolution", "1920x1080",
#                 "--output-audio-encoder", "aac",
#                 "--output-video-encoder", "libx264",
#                 "--output-video-preset", "veryfast",
#                 "--output-video-quality", str(output_video_quality),
#                 "--output-video-resolution", "1080x720",
#                 "--output-video-fps", str(output_video_fps),
#                 "--frame-start", str(frame_start),
#                 "--frame-end", str(frame_end),
#                 "--face-mask-types"
#             ]
            
#             cmd.extend(face_mask_types)
            
#             if skip_audio:
#                 cmd.append("--skip-audio")

#             if face_mask_padding:
#                 cmd.append("--face-mask-padding")
#                 if isinstance(face_mask_padding, list):
#                     cmd.extend([str(p) for p in face_mask_padding])
#                 else:
#                     cmd.append(str(face_mask_padding))
            
#             cmd.append("--processors")
#             cmd.extend(processors.split(','))
            
#             cmd.extend([
#                 "--face-enhancer-model", "gfpgan_1.4",
#                 "--face-swapper-model", "inswapper_128",
#                 "--execution-providers", "cuda",
#                 "--execution-thread-count", "4",
#                 "--execution-queue-count", "1",
#                 "--log-level", "debug"
#             ])
            
#             print(f"[Iteration {iteration_number}] Running FaceFusion with command: {' '.join(cmd)}")
            
#             try:
#                 process = subprocess.Popen(
#                     cmd,
#                     stdout=subprocess.PIPE,
#                     stderr=subprocess.PIPE,
#                     universal_newlines=True
#                 )
                
#                 print(f"[Iteration {iteration_number}] Processing frames {frame_start} to {frame_end}...")
                
#                 from threading import Thread
#                 import queue
#                 stdout_queue = queue.Queue()
#                 stderr_queue = queue.Queue()
                
#                 def read_stdout():
#                     for line in iter(process.stdout.readline, ""):
#                         if "%" in line:
#                             print(f"\r[Iteration {iteration_number}] Processing: {line.strip()}", end="")
#                         else:
#                             print(line.strip())
#                         stdout_queue.put(line)
#                     process.stdout.close()
                
#                 def read_stderr():
#                     for line in iter(process.stderr.readline, ""):
#                         print(f"ERROR: {line.strip()}")
#                         stderr_queue.put(line)
#                     process.stderr.close()
                
#                 stdout_thread = Thread(target=read_stdout, daemon=True)
#                 stderr_thread = Thread(target=read_stderr, daemon=True)
#                 stdout_thread.start()
#                 stderr_thread.start()
                
#                 return_code = process.wait()
#                 print("")
                
#                 if return_code != 0:
#                     stderr_output = ""
#                     try:
#                         while not stderr_queue.empty():
#                             stderr_output += stderr_queue.get_nowait()
#                     except queue.Empty:
#                         pass
#                     if "CUDA out of memory" in stderr_output:
#                         raise RuntimeError("GPU ran out of memory. Try processing a smaller video or reducing resolution.")
#                     elif "No face detected" in stderr_output:
#                         raise ValueError("No faces could be detected in the source image. Please try another image.")
#                     else:
#                         raise RuntimeError(f"FaceFusion failed with error code {return_code}: {stderr_output}")
                
#                 print(f"[Iteration {iteration_number}] Verifying output file...")
#                 if not os.path.exists(iteration_output) or os.path.getsize(iteration_output) == 0:
#                     raise RuntimeError(f"Output file not created or empty: {iteration_output}")
                
#                 print(f"[Iteration {iteration_number}] Successfully processed frames {frame_start} to {frame_end}")
                
#                 if iteration < iterations - 1:
#                     current_target = iteration_output
                
#             except Exception as e:
#                 print(f"Error during processing iteration {iteration_number}: {str(e)}")
#                 for filename in os.listdir(temp_dir):
#                     filepath = os.path.join(temp_dir, filename)
#                     try:
#                         os.unlink(filepath)
#                     except:
#                         pass
#                 try:
#                     os.rmdir(temp_dir)
#                 except:
#                     pass
#                 raise
        
#         print("\nAll iterations completed successfully!")
#         print(f"Final output saved to: {final_output_path}")
        
#         print("Cleaning up temporary files...")
#         for filename in os.listdir(temp_dir):
#             filepath = os.path.join(temp_dir, filename)
#             try:
#                 os.unlink(filepath)
#             except Exception as e:
#                 print(f"Warning: Could not delete temporary file {filepath}: {str(e)}")
#         try:
#             os.rmdir(temp_dir)
#         except Exception as e:
#             print(f"Warning: Could not delete temporary directory {temp_dir}: {str(e)}")
        
#         return Path(final_output_path)

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
        print("Setting up FaceFusion for female video processing...")
    
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
        """Run face swap with FaceFusion using multiple iterations for different frame ranges."""
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
        
        # Define the specific frame ranges and settings for each iteration,
        # including a per-iteration reference face position override.
        iterations_config = [
            {
                "frame_start": 0,
                "frame_end": 61,
                "reference_frame_number": 19,
                "reference_face_position": 1,  # Override: use position 1 for this segment
                "face_mask_types": ["occlusion", "region"],
                "face_mask_padding": None,
                "reference_face_distance": 0.65,
                "skip_audio": True    # Default value
            },
            {
                "frame_start": 62,
                "frame_end": 105,
                "reference_frame_number": 100,
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region", "box"],
                "face_mask_padding": [45, 23, 0, 22],
                "reference_face_distance": 0.65,
                "skip_audio": True
            },
            {
                "frame_start": 106,
                "frame_end": 147,
                "reference_frame_number": 106,  # Using start frame as reference
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region", "box"],
                "face_mask_padding": [0, 42, 35, 42],
                "reference_face_distance": 0.65,
                "skip_audio": True
            },
            {
                "frame_start": 148,
                "frame_end": 241,
                "reference_frame_number": 198,
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region", "box"],
                "face_mask_padding": [0, 42, 35, 42],
                "reference_face_distance": 0.65,
                "skip_audio": True
            },
            {
                "frame_start": 242,
                "frame_end": 565,
                "reference_frame_number": 479,
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region"],
                "face_mask_padding": None,
                "reference_face_distance": 0.65,
                "skip_audio": True
            },
            {
                "frame_start": 583,
                "frame_end": 625,
                "reference_frame_number": 605,  # Using start frame as reference
                "reference_face_position": 0,
                "face_mask_types": ["occlusion", "region", "box"],
                "face_mask_padding": [45, 0, 0, 0],  # Single value expanded to all sides
                "reference_face_distance": 0.8,
                "skip_audio": True
            }
        ]
        
        iterations = len(iterations_config)
        
        print(f"Preparing to run {iterations} iterations with frame ranges:")
        for i, config in enumerate(iterations_config):
            start = config["frame_start"]
            end = config["frame_end"]
            print(f"  Iteration {i+1}: Frames {start} to {end} (Ref frame: {config['reference_frame_number']}, Ref pos: {config['reference_face_position']})")
        
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
        
         #NEW: Extract Audio Once from the Original Target Video
        audio_temp_path = os.path.join(tempfile.gettempdir(), f"temp_audio_{timestamp}.aac")
        print("Extracting audio from original target video...")
        # This command extracts the audio track without re-encoding (-c:a copy)
        cmd_audio = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(target),
            "-vn", "-c:a", "copy",
            "-y", audio_temp_path
        ]
        subprocess.run(cmd_audio, check=True)
        print(f"Audio extracted to: {audio_temp_path}")

        # Current target for the first iteration
        current_target = str(target)
        
        # Process each iteration
        for iteration, config in enumerate(iterations_config):
            iteration_number = iteration + 1
            frame_start = config["frame_start"]
            frame_end = config["frame_end"]
            reference_frame_number = config["reference_frame_number"]
            ref_face_pos = config["reference_face_position"]
            face_mask_types = config["face_mask_types"]
            face_mask_padding = config["face_mask_padding"]
            reference_face_distance = config["reference_face_distance"]
            skip_audio = config["skip_audio"]
            
            print(f"\n[Iteration {iteration_number}/{iterations}] Processing frames {frame_start} to {frame_end}...")
            
            # Define output for this iteration
            if iteration == iterations - 1:
                iteration_output = final_output_path
            else:
                iteration_output = os.path.join(temp_dir, f"temp_output_iteration_{iteration_number}.mp4")
            
            # Build command for this iteration
            cmd = [
                "python", facefusion_script, "headless-run",
                "-s", str(source),
                "-t", current_target,
                "-o", iteration_output,
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
                "--output-video-preset", "veryfast",
                "--output-video-quality", str(output_video_quality),
                "--output-video-resolution", "1080x720",
                "--output-video-fps", str(output_video_fps),
                "--frame-start", str(frame_start),
                "--frame-end", str(frame_end),
                "--face-mask-types"
            ]
            
            cmd.extend(face_mask_types)
            
            if skip_audio:
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
            
            print(f"[Iteration {iteration_number}] Running FaceFusion with command: {' '.join(cmd)}")
            
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                print(f"[Iteration {iteration_number}] Processing frames {frame_start} to {frame_end}...")
                
                from threading import Thread
                import queue
                stdout_queue = queue.Queue()
                stderr_queue = queue.Queue()
                
                def read_stdout():
                    for line in iter(process.stdout.readline, ""):
                        if "%" in line:
                            print(f"\r[Iteration {iteration_number}] Processing: {line.strip()}", end="")
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
                
                print(f"[Iteration {iteration_number}] Verifying output file...")
                if not os.path.exists(iteration_output) or os.path.getsize(iteration_output) == 0:
                    raise RuntimeError(f"Output file not created or empty: {iteration_output}")
                
                print(f"[Iteration {iteration_number}] Successfully processed frames {frame_start} to {frame_end}")
                
                if iteration < iterations - 1:
                    current_target = iteration_output
                
            except Exception as e:
                print(f"Error during processing iteration {iteration_number}: {str(e)}")
                for filename in os.listdir(temp_dir):
                    filepath = os.path.join(temp_dir, filename)
                    try:
                        os.unlink(filepath)
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
                raise
        
        print("\nAll iterations completed successfully!")
        print(f"Final output saved to: {final_output_path}")
        
         #NEW: Merge the previously extracted audio with the final video
        final_video_with_audio = final_output_path.replace(".mp4", "_final.mp4")
        print("Merging extracted audio with the final video...")
        cmd_merge_audio = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", final_output_path,
            "-i", audio_temp_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-y", final_video_with_audio
        ]
        subprocess.run(cmd_merge_audio, check=True)
        print(f"Audio merged successfully. Final video with audio saved to: {final_video_with_audio}")
        final_output_path = final_video_with_audio

        # Clean up temporary files
        print("Cleaning up temporary files...")
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            try:
                os.unlink(filepath)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {filepath}: {str(e)}")
        try:
            os.rmdir(temp_dir)
        except Exception as e:
            print(f"Warning: Could not delete temporary directory {temp_dir}: {str(e)}")

        try:
            os.unlink(audio_temp_path)
        except Exception as e:
            print(f"Warning: Could not delete temporary audio file {audio_temp_path}: {str(e)}")
        
        return Path(final_output_path)
