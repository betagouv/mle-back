import requests
from bs4 import BeautifulSoup
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from geopy.geocoders import BANFrance

from accommodation.models import ExternalSource
from accommodation.serializers import AccommodationImportSerializer
from account.models import Owner


class Command(BaseCommand):
    help = "Scrape student residences from Agefo"

    BASE_URL = "https://agefo.com"

    def handle(self, *args, **kwargs):
        url = f"{self.BASE_URL}/wp-admin/admin-ajax.php"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(
            url,
            headers=headers,
            data={
                "postPerPage": "100",
                "postType": "residence",
                "typeResidence": "5",
                "offset": 0,
                "action": "ajaxLoadMore",
            },
        )

        if response.status_code != 200:
            self.stderr.write(f"Error {response.status_code} accessing the site")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        residence_cards = soup.find_all("article", class_="card-residence")

        for card in residence_cards:
            name_tag = card.find("h3")
            link_tag = card.find("a", href=True)

            name = name_tag.text.strip() if name_tag else None
            if not name:
                self.stderr.write("Ignoring accommodation without name")
                continue

            link = link_tag["href"] if link_tag else None

            owner = Owner.get_or_create(data={"name": "Agefo", "url": self.BASE_URL})

            details_data = self.get_residence_details(link)

            serializer = AccommodationImportSerializer(
                data={
                    "name": name,
                    "published": True,
                    "residence_type": "universitaire-conventionnee",
                    "source": ExternalSource.SOURCE_AGEFO,
                    "source_id": link.split("/")[-2],
                    "owner": owner,
                    **details_data,
                }
            )

            if serializer.is_valid():
                accommodation = serializer.save()
                self.stdout.write(f"Details added for {accommodation.name}")
            else:
                self.stderr.write(f"Error saving residence: {serializer.errors}")

    def _get_images_data(self, image_srcs):
        if not image_srcs:
            return

        images = []

        image_srcs = set([src for src in image_srcs if src.startswith(self.BASE_URL)])
        for image_url in image_srcs:
            image_response = requests.get(image_url)

            if image_response.status_code == 200:
                images.append(image_response.content)
            else:
                self.stderr.write(f"Error retrieving image {image_url}: {image_response.status_code}")

        return images

    def get_residence_details(self, url):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self.stderr.write(f"Error {response.status_code} accessing {url}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        price_tag = soup.select_one("div.container .onglet-text p:first-of-type strong")
        price = price_tag.text.replace(" €", "").strip() if price_tag else None

        onglet_text = soup.find("div", class_="onglet-text")
        address = onglet_text.find_all("p")[-1].text.strip() if onglet_text and onglet_text.find_all("p") else None

        geolocator = BANFrance()
        location = geolocator.geocode(address)

        city = location.raw["properties"]["city"]
        address = location.raw["properties"]["name"]
        postal_code = location.raw["properties"]["postcode"]
        geom = Point(location.longitude, location.latitude, srid=4326)

        main_image = soup.select_one(".hero .items-end img")["src"]
        image_tags = soup.select(".galleryWithThumbnail img")
        image_urls = [main_image] + [img["src"] for img in image_tags if "src" in img.attrs]

        return {
            "city": city,
            "postal_code": postal_code,
            "address": address,
            "geom": geom,
            "images": self._get_images_data(image_urls),
            "price_min_t1": price,
        }
