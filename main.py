import requests
import json
import os
from tqdm import tqdm
from datetime import datetime
from config import token_vk


class VkBackupPhotos:
    """
    Класс для загрузки фотографий из профиля VK по идентификатору
    и токену полученному из Я.Полигона.
    Записывает название и тип фото в файл photos_info.json,
    затем выводит на экран данные и ссылку куда загружены фото.

    ...

    Атрибуты класса
    -----------
        identifier_vk : str
            Идентификатор странички пользователя в VK.
        token_yndx_disk : str
            Токен пользователя из Я.Полигона.
        quantity_photo : int
            Количетсво загружаемых фотографий (по умолчанию 5).

    Методы класса
    -----------
    get_photos():
        Получает список всех фотографий из профиля пользователя.
    largest_image_likes_type(list_url_image: list):
        Получает фотографию самого высокого качетва, название типа и количество лайков.
    creat_folder(folder_name: str):
        Создает папку с название vkphotos_backup на Я.Диске пользователя.
    download_and_in_yadisk():
        Загружает на Я.Диск фото самого высокого качества
        и называет его в зависимости от количества лайков.
    """

    def __init__(self, identifier_vk: str, token_yndx_disk: str, quantity_photo=5):
        """
        Устанавливаем все необходимые атрибуты для VkBackupPhotos.

        Параметры
        -----------
        identifier_vk : str
            Идентификатор странички пользователя в VK
        token_yndx_disk : str
            Токен пользователя из Я.Полигона
        quantity_photo : int
            Количетсво загружаемых фотографий (по умолчанию 5)
        """

        if identifier_vk == '':
            print('Вы не ввели идентификатор VK')
            return
        elif identifier_vk.isdigit():
            self.__identifier_vk = identifier_vk
        else:
            print('Идентификатор должен состоять только из цифр')
            return

        if token_yndx_disk == '':
            print('Вы не ввели токен из Я.Диска')
            return
        else:
            self.__token_yndx_disk = token_yndx_disk
        self.__quantity_photo = quantity_photo
        self.url_api_vk = 'https://api.vk.com/method'
        self.url_api_yadisk = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.download_and_in_yadisk()

    def get_photos(self) -> dict:
        """
        Передает идентификатор введенный пользователем и
        возвращает словарь с параметрами каждой фотографии из профиля.
        """

        params = {
            'access_token': token_vk,
            'v': '5.199',
            'owner_id': self.__identifier_vk,
            'album_id': 'profile',
            'rev': '0',
            'extended': '1'
            }
        response_image_vk = requests.get(
            f'{self.url_api_vk}'
            f'/photos.get', params=params
        )
        return response_image_vk.json()

    def largest_image_likes_type(self, list_url_image: list) -> list:
        """
        Опеределяет фотографию самого высокого качества, количество лайков и тип.

        Параметры
        -----------
        list_url_image : list
            Список полученный из метода get_photos() по ключам словаря ['response']['items']

        Возвращает
        -----------
        Срез списка в зависимости от необходимого количества фотографий в формате
        [url фотографии, лайки, тип].
        """

        type_picture = {
            's': 0,
            'm': 1,
            'x': 2,
            'o': 3,
            'p': 4,
            'q': 5,
            'r': 6,
            'y': 7,
            'z': 8,
            'w': 9
        }
        types_all = []
        for item_image in list_url_image:
            types = {}
            for image_size in item_image['sizes']:
                types[image_size['url']] = image_size['type']
            largest_url = max(types.items(), key=lambda item: type_picture[item[1]])[0]
            types_all.append(
                [largest_url,
                item_image['likes']['count'],
                image_size['type']]
            )
        return types_all[:self.__quantity_photo]
    
    def creat_folder(self, folder_name: str) -> str:
        """
        Передает токен Я.Диска введенный пользователем и
        создает папку vkphotos_backup на диске.

        Параметры
        -----------
        folder_name: str
            Имя папки

        Возвращает
        -----------
        Название папки. 
        При возникновении ошибки в запросе,
        возвращает ответ в формате json для последующей обработки.
        """
        
        params = {
        'path': folder_name
        }
        headers = {
        'Authorization': self.__token_yndx_disk,
        'Content-Type': 'application/json'
        }
        response = requests.put(
            f'{self.url_api_yadisk}',
            headers=headers,
            params=params
        )
        try:
            'error' in response.json()
        except KeyError:
            return folder_name
        else:
            return response.json()
        
    def download_and_in_yadisk(self):
        """
        Загружает фотографию на Я.Диск пользователя, в папку vkphotos_backup
        с названием исходя из количества лайков.
        При уже существующем названии, добавляет дату и время загрузки.

        Возвращает
        -----------
        None
        """
        
        name_folder = self.creat_folder('vkphotos_backup')
        try:
            if 'уже существует папка' in name_folder['message']:
                name_folder = 'vkphotos_backup'
            elif name_folder['error']:
                print(name_folder['message'])
                return
        except KeyError:
            name_folder = 'vkphotos_backup'

        now = datetime.now()
        headers = {
            'Authorization': self.__token_yndx_disk,
            'Content-Type': 'application/json'
        }
        images_likes_type = (
            self.largest_image_likes_type(self.get_photos()['response']['items'])
        )
        if not images_likes_type:
            print("Нет изображений для загрузки.")
            return
        set_image = set()
        data_image_vk = []
        for url_image, likes, types in tqdm(images_likes_type, desc='Загрузка фото'):
            if likes in set_image:
                likes = f'{likes}_{now.date()}_{now.hour}_{now.minute}_{now.second}'
            set_image.add(likes)
            params = {
                'path': f'disk:/{name_folder}/{likes}.jpg',
                'url': url_image
            }
            response = requests.post(
                f'{self.url_api_yadisk}/upload',
                params=params,
                headers=headers
            )
            if 'error' in response.json():
                print(
                    f'При загрузке фото {url_image} возникла ошибка {response.json()['message']}'
                )
                continue
            data = {
                'file_name': f'{likes}',
                'size': f'{types}'
            }
            data_image_vk.append(data)

        with open('photos_info.json', 'w', encoding='utf-8') as f:
            json.dump(data_image_vk, f, ensure_ascii=False, indent=2)
            print(json.dumps(data_image_vk, indent=2))

        print(
            'Фото добавились по ссылке https://disk.yandex.ru/client/disk/vkphotos_backup'
        )


os.environ['identifiter'] = input('Введите идентификатор странички в ВК: ')
os.environ['token_yndx_disk'] = input('Введите токен из полигона Яндекс: ')
number_of_photos = input('Укажите желаемое количество '
                         'копируемых фотографий(по умолчанию 5): ')
if number_of_photos == '':
    number_of_photos = 5
VkBackupPhotos(os.environ['identifiter'],
               os.environ['token_yndx_disk'],
               int(number_of_photos))