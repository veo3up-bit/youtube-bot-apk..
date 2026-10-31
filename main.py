import flet as ft
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def main(page: ft.Page):
    page.title = "YouTube Bot"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    selected_file_path = ft.Text(value="No video selected", color=ft.colors.GREY_400)
    status_log = ft.Text(value="Status: Ready", color=ft.colors.GREEN_400)

    access_token_input = ft.TextField(
        label="Access Token",
        password=True,
        can_reveal_password=True,
        hint_text="Paste your YouTube Token here"
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

    def get_youtube_service():
        if not access_token_input.value:
            status_log.value = "Error: Enter Access Token first!"
            status_log.color = ft.colors.RED_400
            page.update()
            return None
        creds = Credentials(token=access_token_input.value)
        return build('youtube', 'v3', credentials=creds)

    def upload_video_action(e):
        youtube = get_youtube_service()
        if not youtube or selected_file_path.value == "No video selected":
            return
        try:
            status_log.value = "Uploading... Please wait."
            page.update()
            body = {
                'snippet': {
                    'title': title_input.value or "New Video",
                    'description': desc_input.value or "",
                    'categoryId': "20"
                },
                'status': {
                    'privacyStatus': privacy_dropdown.value,
                    'selfDeclaredMadeForKids': False
                }
            }
            media = MediaFileUpload(selected_file_path.value, chunksize=-1, resumable=True)
            response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
            status_log.value = f"Uploaded! ID: {response['id']}"
            status_log.color = ft.colors.GREEN_400
        except Exception as ex:
            status_log.value = f"Error: {str(ex)}"
            status_log.color = ft.colors.RED_400
        page.update()

    def reply_comments_action(e):
        youtube = get_youtube_service()
        if not youtube or not video_id_input.value:
            return
        try:
            response = youtube.commentThreads().list(part="snippet", videoId=video_id_input.value, maxResults=10).execute()
            count = 0
            for item in response.get('items', []):
                if item['snippet']['totalReplyCount'] == 0:
                    reply_body = {'snippet': {'parentId': item['id'], 'textOriginal': reply_text_input.value}}
                    youtube.comments().insert(part="snippet", body=reply_body).execute()
                    count += 1
            status_log.value = f"Replied to {count} comments!"
            status_log.color = ft.colors.GREEN_400
        except Exception as ex:
            status_log.value = f"Error: {str(ex)}"
            status_log.color = ft.colors.RED_400
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
