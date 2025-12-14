import aiohttp
import os
from config.settings import IMAGE_PROVIDER, IMAGE_API_KEY
import json
import base64


class ImageGenerator:

    def __init__(self):
        self.provider = IMAGE_PROVIDER.lower()
        self.api_key = IMAGE_API_KEY

    async def generate_image(self, prompt: str, article_title: str = None) -> dict:
        try:
            if self.provider == 'kandinsky':
                return await self._generate_kandinsky(prompt)
            elif self.provider == 'gigachat':
                return await self._generate_gigachat_image(prompt)
            elif self.provider == 'yandex':
                return await self._generate_yandex_art(prompt)
            elif self.provider == 'baidu':
                return await self._generate_baidu(prompt)
            elif self.provider == 'openai':
                return await self._generate_dalle(prompt)
            elif self.provider == 'stability':
                return await self._generate_stability(prompt)
            else:
                return await self._generate_fusionbrain(prompt, article_title)
        except Exception as e:
            print(f"Ошибка генерации изображения: {e}")
            return await self._generate_fusionbrain(prompt, article_title or "Новость")

    async def _generate_kandinsky(self, prompt: str) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api-key.fusionbrain.ai/key/api/v1/text2image/run',
                    headers={
                        'X-Key': f'Key {self.api_key}',
                        'X-Secret': f'Secret {os.getenv("KANDINSKY_SECRET", "")}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'type': 'GENERATE',
                        'numImages': 1,
                        'width': 1024,
                        'height': 1024,
                        'generateParams': {
                            'query': prompt
                        }
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        uuid = data['uuid']

                        check_url = f'https://api-key.fusionbrain.ai/key/api/v1/text2image/status/{uuid}'
                        async with session.get(check_url, headers={
                            'X-Key': f'Key {self.api_key}',
                            'X-Secret': f'Secret {os.getenv("KANDINSKY_SECRET", "")}'
                        }) as check_response:
                            if check_response.status == 200:
                                result = await check_response.json()
                                if result['status'] == 'DONE':
                                    return {
                                        'success': True,
                                        'base64': result['images'][0],
                                        'provider': 'Kandinsky (Fusion Brain)'
                                    }

                    return {
                        'success': False,
                        'error': 'Kandinsky API error'
                    }
        except Exception as e:
            print(f"Kandinsky error: {e}")
            return {'success': False, 'error': str(e)}

    async def _generate_gigachat_image(self, prompt: str) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                token_response = await session.post(
                    'https://ngw.devices.sberbank.ru:9443/api/v2/oauth',
                    headers={
                        'Authorization': f'Basic {self.api_key}',
                        'RqUID': str(os.urandom(16).hex()),
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    data={'scope': 'GIGACHAT_API_PERS'}
                )

                if token_response.status == 200:
                    token_data = await token_response.json()
                    access_token = token_data['access_token']

                    async with session.post(
                        'https://gigachat.devices.sberbank.ru/api/v1/images/generations',
                        headers={
                            'Authorization': f'Bearer {access_token}',
                            'Content-Type': 'application/json'
                        },
                        json={
                            'prompt': prompt,
                            'n': 1,
                            'size': '1024x1024'
                        }
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                'success': True,
                                'base64': data['data'][0]['b64_json'],
                                'provider': 'GigaChat (Сбер)'
                            }

                return {'success': False, 'error': 'GigaChat API error'}
        except Exception as e:
            print(f"GigaChat error: {e}")
            return {'success': False, 'error': str(e)}

    async def _generate_yandex_art(self, prompt: str) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync',
                    headers={
                        'Authorization': f'Api-Key {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'modelUri': f'art://{os.getenv("YANDEX_FOLDER_ID", "")}/yandex-art/latest',
                        'generationOptions': {
                            'seed': 1863,
                            'aspectRatio': {
                                'widthRatio': 1,
                                'heightRatio': 1
                            }
                        },
                        'messages': [
                            {
                                'weight': 1,
                                'text': prompt
                            }
                        ]
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        operation_id = data['id']

                        check_url = f'https://llm.api.cloud.yandex.net:443/operations/{operation_id}'
                        async with session.get(check_url, headers={
                            'Authorization': f'Api-Key {self.api_key}'
                        }) as check_response:
                            if check_response.status == 200:
                                result = await check_response.json()
                                if result.get('done'):
                                    image_base64 = result['response']['image']
                                    return {
                                        'success': True,
                                        'base64': image_base64,
                                        'provider': 'YandexART'
                                    }

                    return {'success': False, 'error': 'YandexART API error'}
        except Exception as e:
            print(f"YandexART error: {e}")
            return {'success': False, 'error': str(e)}

    async def _generate_baidu(self, prompt: str) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl',
                    params={'access_token': self.api_key},
                    headers={'Content-Type': 'application/json'},
                    json={
                        'prompt': prompt,
                        'size': '1024x1024',
                        'n': 1
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'base64': data['data'][0]['b64_image'],
                            'provider': 'Baidu 文心一格'
                        }

                    return {'success': False, 'error': 'Baidu API error'}
        except Exception as e:
            print(f"Baidu error: {e}")
            return {'success': False, 'error': str(e)}

    async def _generate_fusionbrain(self, prompt: str, title: str = None) -> dict:
        colors = ['FF6B6B', '4ECDC4', '45B7D1', '96CEB4', 'FFEAA7', 'DFE6E9']
        bg_color = colors[hash(title or prompt) % len(colors)]
        text_color = 'FFFFFF'

        display_text = (title or prompt)[:50].replace(' ', '+')
        placeholder_url = f'https://via.placeholder.com/1024x1024/{bg_color}/{text_color}?text={display_text}'

        return {
            'success': True,
            'url': placeholder_url,
            'provider': 'Локальный генератор',
            'note': 'Настройте AI_PROVIDER для использования реальной генерации'
        }

    async def _generate_dalle(self, prompt: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.openai.com/v1/images/generations',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'prompt': prompt,
                    'n': 1,
                    'size': '1024x1024',
                    'model': 'dall-e-3'
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'url': data['data'][0]['url'],
                        'provider': 'DALL-E 3'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'DALL-E API error: {response.status}'
                    }

    async def _generate_stability(self, prompt: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'text_prompts': [{'text': prompt}],
                    'cfg_scale': 7,
                    'height': 1024,
                    'width': 1024,
                    'samples': 1,
                    'steps': 30
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'base64': data['artifacts'][0]['base64'],
                        'provider': 'Stability AI'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Stability AI error: {response.status}'
                    }

    async def create_post_image(self, article_data: dict, platform: str) -> dict:
        title = article_data.get('title', '')
        summary = article_data.get('summary', '')
        sentiment = article_data.get('sentiment', 'neutral')

        sentiment_styles = {
            'positive': 'яркие, живые цвета, оптимистичное настроение',
            'negative': 'приглушенные цвета, серьезный тон, профессиональный',
            'neutral': 'сбалансированные цвета, чистый дизайн, современный'
        }

        style = sentiment_styles.get(sentiment, 'современный, профессиональный')

        platform_styles = {
            'telegram': 'пост для социальных сетей, привлекающий внимание',
            'vk': 'графика для соцсетей, дружелюбная',
            'twitter': 'минималистичная, стиль карточки twitter',
            'linkedin': 'профессиональная, бизнес-презентация',
            'press': 'формальная, заголовок пресс-релиза'
        }

        platform_style = platform_styles.get(platform, 'современная соцсеть')

        prompt = f"Создай {platform_style} изображение для статьи: {title[:100]}. Стиль: {style}. Абстрактное, без текста, профессиональный дизайн."

        return await self.generate_image(prompt, title)
