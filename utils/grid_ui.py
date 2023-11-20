from abc import ABC, abstractmethod
from operator import truediv
from pickletools import stackslice
from typing import Callable
import streamlit as st
import pandas as pd
import math


class ResultModel:
    def __init__(self, artisan: str, craftID: int, url: str,
                 actual_product_image: Callable,
                 creation_information: Callable,
                 default_product_image: str):
        self._default_product_image = None
        if default_product_image is None:
            self._default_product_image = "https://cdn1.vectorstock.com/i/thumb-large/46/50/missing-picture-page-for-website-design-or-mobile-vector-27814650.jpg"
        self._url = url
        self._artisan = artisan
        self._craftID = craftID
        self._actual_product_image = actual_product_image(self.artisan, self.craftID)
        self._creation_infomation = creation_information(self.artisan, self.craftID)

    @property
    def url(self):
        return self._url

    @property
    def artisan(self):
        return self._artisan

    @property
    def craftID(self):
        return self._craftID

    @property
    def creation_information(self):
        return self._creation_infomation

    def image(self):
        image_to_return = self._default_product_image
        if self._actual_product_image is not None:
            image_to_return = self._actual_product_image
        return image_to_return

class EtsyView(ResultModel):
    def draw(self, column):
        with column.container():
            column.image(self.image())
            column.markdown(
                ", ".join(self.creation_information) +
                "</br>"
                f"by: {self.artisan} [click to see more]({self.url})", unsafe_allow_html=True
            )

class GridViewer:
    def __init__(self, results: list, columns_per_row: int=4, ):
        self._results = results
        self._number_of_results = len(results)
        self._columns_per_row = columns_per_row
        self._number_of_rows = math.ceil(self._number_of_results/columns_per_row)

    def _update_layout(self, number_of_results=True, number_rows=False):
        if number_of_results:
            self._number_of_results = len(self._results)

        if number_rows:
            self._number_of_rows = math.ceil(self._number_of_results/self._columns_per_row)

    @property
    def columns_per_row(self):
        return self._columns_per_row

    @columns_per_row.setter
    def columns_per_row(self, number):
        self._columns_per_row = number

    @property
    def results(self):
        return self._results

    @results.setter
    def results(self, results):
        self._results = results
        self._update_layout()

    def draw(self, this_container: st.container):
        # streamlit is oriented around a vertical model of stacking
        # ... so we can create a grid of results by stacking columns
        with this_container:
            use_this_to = 0 # index
            for _ in range(self._number_of_rows):
                the_columns = st.columns(self._columns_per_row)
                for a_column in the_columns:
                    if use_this_to < self._number_of_results:
                        self._results[use_this_to].draw(a_column)
                    use_this_to += 1

    def draw_in_st(self, st: st):
        use_this_to = 0 # index
        for _ in range(self._number_of_rows):
            the_columns = st.columns(self._columns_per_row)
            for a_column in the_columns:
                if use_this_to < self._number_of_results:                
                    self._results[use_this_to].draw(
                        a_column
                    )
                    use_this_to += 1

if __name__ == "__main__":
    """
    Poor man's visual integration test
    """
    def actual(artisan, craftID):
        return "https://westbh.com/images/product/b/boots-mens-rust-carpincho-chelsea-boot-256px-256px.jpg"

    def info(artisan, craftID):
        return ['african american', 'black owned', 'women owned']

    etsy = EtsyView(artisan='Akoma', craftID=123, url="www.example.com",
                    actual_product_image=actual, creation_information=info, default_product_image=None)

    etsy = GridViewer([etsy for _ in range(9)])

    here = st.container()

    etsy.draw(here)

    # issue: here.empty() does not clear container
    del here
    here = st.container()
    here.empty()

    # okay let uh change the number of columns
    etsy.columns_per_row = 3
    etsy._update_layout(number_of_results=False, number_rows=True)
    etsy.draw(here)