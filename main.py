import flet as ft
import requests
import json
import os

def main(page: ft.Page):
    page.title = "YouTube Bot Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    selected_file_path = ft.Text(value="No video selected")
    status_log = ft.Text(value="Status: Ready")

    access_token_input = ft.TextField(
        label="Access Token",
        password=True,
        can_reveal_password=True,
        hint_text="Paste your YouTube Access Token here"
    )
    title_input = ft.TextField(label="Video Title")
    desc_input = ft.TextField(label="Video Description", multiline=True, min_lines=3)
    privacy_dropdown = ft.Dropdown(
        label="Privacy",
        value="public",
        options=[
            ft.dropdown.Option("public"),
            ft.dropdown.Option("unlisted"),
            ft.dropdown.Option("private"),
        ]
    )
    video_id_input = ft.TextField(label="Video ID (for comments)")
    reply_text_input = ft.TextField(label="Auto-Reply Message")

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            selected_file_path.value = e.files[0].path
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def upload_video_action(e):
        token = access_token_input.value.strip()
        file_path = selected_file_path.value
        if not token or file_path == "No video selected":
            status_log.value = "Error: Enter Access Token and select a video!"
            page.update()
            return

        try:
            status_log.value = "Uploading video... Please wait."
            page.update()

            headers = {
                "Authorization": f"Bearer {token}",
            }
            metadata = {
                "snippet": {
                    "title": title_input.value or "New Video",
                    "description": desc_input.value or "",
                    "categoryId": "20"
                },
                "status": {
                    "privacyStatus": privacy_dropdown.value,
                    "selfDeclaredMadeForKids": False
                }
            }

            with open(file_path, "rb") as video_file:
                files = {
                    "data": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
                    "file": (os.path.basename(file_path), video_file, "application/octet-stream")
                }
                url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status"
                response = requests.post(url, headers=headers, files=files)

            if response.status_code == 200:
                vid_id = response.json().get("id")
                status_log.value = f"Success! Uploaded Video ID: {vid_id}"
            else:
                status_log.value = f"API Error: {response.text}"
        except Exception as ex:
            status_log.value = f"Error: {str(ex)}"
        page.update()

    def reply_comments_action(e):
        token = access_token_input.value.strip()
        vid_id = video_id_input.value.strip()
        reply_msg = reply_text_input.value.strip()

        if not token or not vid_id or not reply_msg:
            status_log.value = "Error: Fill Token, Video ID, and Reply message!"
            page.update()
            return

        try:
            status_log.value = "Checking comments..."
            page.update()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            list_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={vid_id}&maxResults=10"
            res = requests.get(list_url, headers=headers)

            if res.status_code != 200:
                status_log.value = f"Error fetching comments: {res.text}"
                page.update()
                return

            items = res.json().get("items", [])
            count = 0
            for item in items:
                if item["snippet"]["totalReplyCount"] == 0:
                    parent_id = item["id"]
                    reply_body = {
                        "snippet": {
                            "parentId": parent_id,
                            "textOriginal": reply_msg
                        }
                    }
                    post_url = "https://www.googleapis.com/youtube/v3/comments?part=snippet"
                    r = requests.post(post_url, headers=headers, json=reply_body)
                    if r.status_code == 200:
                        count += 1

            status_log.value = f"Success! Replied to {count} comments."
        except Exception as ex:
            status_log.value = f"Error: {str(ex)}"
        page.update()

    page.add(
        ft.Text("YouTube Bot Manager", size=24, weight=ft.FontWeight.BOLD),
        status_log,
        ft.Divider(),
        access_token_input,
        ft.Divider(),
        ft.ElevatedButton("1. Choose Video", on_click=lambda _: file_picker.pick_files(allow_multiple=False)),
        selected_file_path,
        title_input,
        desc_input,
        privacy_dropdown,
        ft.ElevatedButton("2. Upload to YouTube", on_click=upload_video_action),
        ft.Divider(),
        video_id_input,
        reply_text_input,
        ft.ElevatedButton("3. Auto-Reply Comments", on_click=reply_comments_action)
    )

ft.app(target=main)
