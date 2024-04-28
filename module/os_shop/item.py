from typing import List
from module.logger import logger
from module.statistics.item import Item, ItemGrid


class OSShopItem(Item):
    def __init__(self, image, button, shop_index, scroll_pos):
        super().__init__(image, button)
        self.shop_index = shop_index
        self.scroll_pos = scroll_pos

    def is_known_item(self) -> bool:
        if self.name == 'DefaultItem':
            return False
        elif 'Empty' in self.name:
            return False
        elif self.name.isdigit():
            return False
        else:
            return True


class OSShopItemGrid(ItemGrid):
    def predict(self, image, shop_index, scroll_pos) -> List[Item]:
        """
        Args:
            image (np.ndarray):
            shop_index (bool): If predict shop index.
            scroll_pos (bool): If predict scroll position.

        Returns:
            list[Item]:
        """
        self._load_image(image)
        amount_list = [item.crop(self.amount_area) for item in self.items]
        amount_list = self.amount_ocr.ocr(amount_list, direct_ocr=True)
        name_list = [self.match_template(item.image) for item in self.items]
        cost_list = [self.match_cost_template(item) for item in self.items]
        price_list = [item.crop(self.price_area) for item in self.items]
        price_list = self.price_ocr.ocr(price_list, direct_ocr=True)
        ignore = 0
        items = []

        for i, a, n, c, p in zip(self.items, amount_list, name_list, cost_list, price_list):
            if (p <= 0):
                ignore += 1
                continue
            i.amount = a
            i.name = n
            i.cost = c
            i.price = p
            if shop_index:
                i.shop_index = shop_index
            if scroll_pos:
                i.scroll_pos = scroll_pos
            items.append(i)

        if ignore > 0:
            logger.warning(f'Ignore {ignore} items, because price <= 0')

        return items
