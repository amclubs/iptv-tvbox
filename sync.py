import requests
import os

# 环境变量
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
SOURCE_REPO = 'o0HalfLife0o/TVBoxOSC'
TARGET_REPO = 'amclubs/iptv-tvbox'

# Headers for GitHub API
headers = {'Authorization': f'token {GITHUB_TOKEN}'}

def log(message):
    print(message)

def check_response(response):
    if response.status_code not in [200, 201]:
        raise Exception(f"Request failed: {response.status_code} - {response.text}")

try:
    # 获取目标仓库的所有发布
    target_releases_url = f'https://api.github.com/repos/{TARGET_REPO}/releases'
    response = requests.get(target_releases_url, headers=headers)
    check_response(response)
    target_releases = response.json()
    target_release_tags = {release['tag_name'] for release in target_releases}

    # 获取源仓库的所有发布
    source_releases_url = f'https://api.github.com/repos/{SOURCE_REPO}/releases'
    response = requests.get(source_releases_url, headers=headers)
    check_response(response)
    source_releases = response.json()

    for release in source_releases:
        tag_name = release['tag_name']

        # 检查是否已经存在相同的release
        if tag_name in target_release_tags:
            log(f"Release with tag {tag_name} already exists in target repository. Skipping.")
            continue

        release_name = release['name']
        release_body = release['body']
        draft = release['draft']
        prerelease = release['prerelease']

        # 创建一个新的 release 在目标仓库
        create_release_url = f'https://api.github.com/repos/{TARGET_REPO}/releases'
        release_data = {
            'tag_name': tag_name,
            'name': release_name,
            'body': release_body,
            'draft': draft,
            'prerelease': prerelease
        }
        response = requests.post(create_release_url, json=release_data, headers=headers)
        check_response(response)
        new_release = response.json()

        # 上传资产到新的 release
        for asset in release['assets']:
            asset_url = asset['browser_download_url']
            asset_name = asset['name']

            # 下载资产
            asset_response = requests.get(asset_url, stream=True)
            check_response(asset_response)
            asset_path = os.path.join('/tmp', asset_name)
            with open(asset_path, 'wb') as f:
                for chunk in asset_response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            # 上传资产到新的 release
            upload_url = new_release['upload_url'].replace('{?name,label}', f'?name={asset_name}')
            with open(asset_path, 'rb') as f:
                headers.update({'Content-Type': 'application/octet-stream'})
                upload_response = requests.post(upload_url, headers=headers, data=f)
                check_response(upload_response)

            # 删除下载的文件
            os.remove(asset_path)
            log(f"Uploaded asset {asset_name} to release {release_name}")

    # 获取目标仓库的所有标签
    target_tags_url = f'https://api.github.com/repos/{TARGET_REPO}/tags'
    response = requests.get(target_tags_url, headers=headers)
    check_response(response)
    target_tags = response.json()
    target_tag_names = {tag['name'] for tag in target_tags}

    # 获取源仓库的所有标签
    source_tags_url = f'https://api.github.com/repos/{SOURCE_REPO}/tags'
    response = requests.get(source_tags_url, headers=headers)
    check_response(response)
    source_tags = response.json()

    for tag in source_tags:
        tag_name = tag['name']

        # 检查是否已经存在相同的tag
        if tag_name in target_tag_names:
            log(f"Tag {tag_name} already exists in target repository. Skipping.")
            continue

        tag_sha = tag['commit']['sha']

        # 创建轻量级标签
        ref_url = f'https://api.github.com/repos/{TARGET_REPO}/git/refs'
        ref_data = {
            'ref': f'refs/tags/{tag_name}',
            'sha': tag_sha
        }
        response = requests.post(ref_url, json=ref_data, headers=headers)
        check_response(response)
        log(f"Created tag {tag_name}")

except Exception as e:
    log(f"Error: {e}")
