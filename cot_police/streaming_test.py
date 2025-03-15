#!/usr/bin/env python3
import requests
import json
import argparse
import sys


def stream_ollama_response(
    prompt, model="llama3", target_word=None, case_sensitive=False
):
    """
    Stream a response from Ollama and trigger an action when a specific word is detected.

    Args:
        prompt (str): The prompt to send to Ollama
        model (str): The model to use (default: llama3)
        target_word (str): The word to look for in the response
        case_sensitive (bool): Whether the word matching should be case sensitive
    """
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {"model": model, "prompt": prompt, "stream": True}

    # Prepare for word detection
    if target_word:
        if not case_sensitive:
            target_word = target_word.lower()
            word_detector = lambda text: target_word in text.lower()
        else:
            word_detector = lambda text: target_word in text
    else:
        word_detector = lambda text: False

    word_found = False
    accumulated_text = ""

    try:
        with requests.post(
            url, headers=headers, data=json.dumps(data), stream=True
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                # Parse the JSON response
                chunk = json.loads(line)
                if "response" in chunk:
                    text_chunk = chunk["response"]
                    accumulated_text += text_chunk

                    # Print the chunk to stdout
                    sys.stdout.write(text_chunk)
                    sys.stdout.flush()

                    # Check if the target word is in the accumulated text
                    if (
                        not word_found
                        and target_word
                        and word_detector(accumulated_text)
                    ):
                        word_found = True
                        trigger_action(target_word, accumulated_text)

                # Check if we're done
                if chunk.get("done", False):
                    print("\n")
                    break

    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
        return None

    return accumulated_text


def trigger_action(word, context):
    """
    Trigger an action when the target word is found.

    Args:
        word (str): The word that was found
        context (str): The text context where the word was found
    """
    print(f"\n\n[ACTION TRIGGERED] Found target word: '{word}'")
    print(f"Context: '{context[-50:]}'\n")

    # Add your custom action here
    # For example:
    # - Send a notification
    # - Call another API
    # - Log to a file
    # - etc.


def main():
    parser = argparse.ArgumentParser(
        description="Stream responses from Ollama and trigger actions on specific words"
    )
    parser.add_argument(
        "--prompt", "-p", type=str, required=True, help="The prompt to send to Ollama"
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="llama3",
        help="The model to use (default: llama3)",
    )
    parser.add_argument(
        "--target-word", "-t", type=str, help="The word to look for in the response"
    )
    parser.add_argument(
        "--case-sensitive",
        "-c",
        action="store_true",
        help="Make the word matching case sensitive",
    )

    args = parser.parse_args()

    stream_ollama_response(
        args.prompt, args.model, args.target_word, args.case_sensitive
    )


if __name__ == "__main__":
    main()
