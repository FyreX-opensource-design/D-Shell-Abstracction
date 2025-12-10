#! /usr/bin/env python3

import argparse
import os
import subprocess
import sys


def transcribe(
    model_dir=None,
    timeout=2.0,
    verbose=False,
    print_output=True
):
    """
    Transcribe speech to text using nerd-dictation.
    
    Args:
        model_dir: Path to vosk model directory (default: ./vosk-model)
        timeout: Seconds of silence before auto-ending (default: 2.0)
        verbose: Print verbose output (default: False)
        print_output: Print output to STDOUT (default: True)
    
    Returns:
        str: Transcribed text, or empty string if no text was captured
    """
    # Get paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "STT", "bin", "python3")
    nerd_dictation_path = os.path.join(script_dir, "nerd-dictation")
    
    # Default model directory
    if model_dir is None:
        model_dir = os.path.join(script_dir, "vosk-model")
    
    # Check if virtual environment Python exists
    if not os.path.exists(venv_python):
        # Fall back to system Python if venv doesn't exist
        venv_python = sys.executable
    
    # Check if nerd-dictation exists
    if not os.path.exists(nerd_dictation_path):
        raise FileNotFoundError(f"nerd-dictation file not found at: {nerd_dictation_path}")
    
    # Check if model directory exists
    if not os.path.exists(model_dir):
        raise FileNotFoundError(f"Vosk model directory not found at: {model_dir}")
    
    # Build command
    cmd = [
        venv_python,
        nerd_dictation_path,
        "begin",
        "--vosk-model-dir", model_dir,
        "--output=STDOUT",
        f"--timeout={timeout}"
    ]
    
    if verbose:
        cmd.extend(["--verbose", "1"])
    
    # Run nerd-dictation
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    # Get transcribed text
    transcribed_text = result.stdout.strip() if result.stdout else ""
    
    # Print errors to stderr
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    # Print output to STDOUT if requested (for testing/piping)
    if print_output and transcribed_text:
        print(transcribed_text)
    
    # Return the transcribed text as a string (for programmatic use)
    return transcribed_text


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Speech-to-text transcription using nerd-dictation"
    )
    parser.add_argument(
        "--model",
        "--model-dir",
        dest="model_dir",
        type=str,
        default=None,
        help="Path to vosk model directory (default: ./vosk-model)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Seconds of silence before auto-ending (default: 2.0)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Don't print output to STDOUT (useful when importing as module)"
    )
    
    args = parser.parse_args()
    
    # Run transcription
    transcribed_text = transcribe(
        model_dir=args.model_dir,
        timeout=args.timeout,
        verbose=args.verbose,
        print_output=not args.quiet
    )
    
    # Exit with error code if no text was captured
    if not transcribed_text:
        sys.exit(1)
    
    # Exit with success
    sys.exit(0)


if __name__ == "__main__":
    main()