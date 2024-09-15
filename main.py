import requests
import json
import os
from tqdm import tqdm
from datetime import datetime
from config import token_vk


class VkBackupPhotos:

    def __init__(self, identifier_vk: str, token_yndx_disk: str, quantity_photo=5):
        self.__identifier_vk = identifier_vk
        self.__token_yndx_disk = token_yndx_disk
        self.__quantity_photo = quantity_photo
        self.url_api_vk = 'https://api.vk.com/method'
        self.url_api_yadisk = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.download_and_in_yadisk()

    def get_photos(self) -> dict:
        params = {
            'access_token': token_vk,
            'v': '5.199',
            'owner_id': self.__identifier_vk,
            'album_id': 'profile',
            'rev': '0',
            'extended': '1'
            }
        response_image_vk = requests.get(f'{self.url_api_vk}'
                                         f'/photos.get', params=params)
        return response_image_vk.json()

    def largest_image_likes_type(self, list_url_image: list) -> list:
        type_picture = {'s': 0, 'm': 1, 'x': 2, 'o': 3, 'p': 4,
                        'q': 5, 'r': 6, 'y': 7, 'z': 8, 'w': 9}
        types_all = []
        for item_image in list_url_image:
            types = {}
            for image_size in item_image['sizes']:
                types[image_size['url']] = image_size['type']
            largest_url = max(types.items(), key=lambda item: type_picture[item[1]])[0]
            types_all.append([largest_url,
                              item_image['likes']['count'],
                              image_size['type']])
        return types_all[:self.__quantity_photo]
    
    def only_likes_for_name_image(self) -> list:
        url_and_likes = (self.largest_image_likes_type
                        (self.get_photos()['response']['items']))
        likes = []
        for like in url_and_likes:
            likes.append(like[1])
        return likes
    
    def creat_folder(self, folder_name: str) -> str:
        params = {
        'path': folder_name
        }
        headers = {
        'Authorization': self.__token_yndx_disk,
        'Content-Type': 'application/json'
        }
        response = requests.put(f'{self.url_api_yadisk}',
                                headers=headers,
                                params=params)
        try:
            'уже существует папка' in response.json()['message']
        except KeyError:
            return folder_name
        else:
            return folder_name
        
    def download_and_in_yadisk(self):
        name_folder = self.creat_folder('vkphotos_backup')
        now = datetime.now()
        headers = {
            'Authorization': self.__token_yndx_disk,
            'Content-Type': 'application/json'
        }
        list_name_image = self.only_likes_for_name_image()
        images_likes_type = (self.largest_image_likes_type
                            (self.get_photos()['response']['items']))
        if not images_likes_type:
            print("Нет изображений для загрузки.")
            return
        set_image = set()
        data_image_vk = []
        for i, (url_image, likes, type) in enumerate(tqdm(images_likes_type,
                                                          desc='Загрузка фото')):
            name_image = list_name_image[i]
            if name_image in set_image:
                name_image = f'{name_image}_{now.date()}_{now.hour}_{now.minute}_{now.second}'
            set_image.add(name_image)
            params = {
                'path': f'disk:/{name_folder}/{name_image}.jpg',
                'url': url_image
            }
            requests.post(f'{self.url_api_yadisk}/upload', params=params, headers=headers)
            data = {
                'file_name': f'{name_image}',
                'size': f'{type}'
            }
            data_image_vk.append(data)

        with open('photos_info.json', 'w', encoding='utf-8') as f:
            json.dump(data_image_vk, f, ensure_ascii=False, indent=2)
        
        with open('photos_info.json', 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        print(json.dumps(data_json, indent=1))
        print(
            'Фото добавились по ссылке https://disk.yandex.ru/client/disk/vkphotos_backup'
        )


os.environ['identifiter'] = input('Введите идентификатор странички в ВК: ')
os.environ['token_yndx_disk'] = input('Введите токен из полигона Яндекс: ')
number_of_photos = input('Укажите желаемое количество'
                         'копируемых фотографий(по умолчанию 5): ')
if number_of_photos == '':
    number_of_photos = 5
VkBackupPhotos(os.environ['identifiter'],
               os.environ['token_yndx_disk'],
               int(number_of_photos))

