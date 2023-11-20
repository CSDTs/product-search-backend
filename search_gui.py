from utils.query import ArtisanNeo4jRetriever
from utils.query import RetreiveRerankQuery
from utils.grid_ui import EtsyView, GridViewer
import pandas as pd
import streamlit as st
from abc import ABC

class ArrayIndicesViewer:
    @staticmethod
    def reindex(the_array, the_indices):
        return the_array[the_indices]

    @staticmethod
    def ranking(the_array):
        sorted_array = sorted(the_array)
        return [
            sorted_array.index(
                a_ranking
            ) for a_ranking in the_array
        ]

class ProductSearchController:
    def __init__(self, model=None, view=None, array_viewer=None):
        self.model = model() # we need its retriewer
        self.view = view(self.model.retriever) # ... to a view of the db at time of call
        self.array_viewer = array_viewer()

    def _search(self, text):
        self.view.text = text
        ranking = self.view.method()
        return self.array_viewer.ranking(ranking)

    def search(self, text):
        ranking = self._search(text)
        return self.model.wide_df.loc[ranking].reset_index(drop=True)

columns_to_display =[
    "product", "the_artisan", "principles", "url"
]

prod = ProductSearchController(
    ArtisanNeo4jRetriever,
    RetreiveRerankQuery,
    ArrayIndicesViewer
)

class PrincipleFilterController:
    def __init__(self, results: pd.DataFrame):
        self.results = results
    def filter_on(self, principles=None):
        use_these_indices = show_this_df.principles.str.contains(
            "|".join(selected_filters)
        )
        return self.results[use_these_indices]

# Stub search
base_df = prod.search('pencil')
filter = PrincipleFilterController(base_df)

if 'model' not in st.session_state:
    st.session_state.model = base_df

if 'filters' not in st.session_state:
    st.session_state.filters = []

if 'selected_filters' not in st.session_state:
    st.session_state.selected_filters = None

class ResultState:
    def __init__(self, inital_results: pd.DataFrame):
        self._results = inital_results
        self._filter = None

    @property
    def filter(self, filter):
        self._filter = filter

    @filter.setter
    def filter(self, filter):
        self._filter = filter

    @property
    def results(self, results):
        self.results = results

    @results.getter
    def results(self):
        show_this_df = self._results
        if self._filter is not None:
            use_these_indices = self._results.principles.str.contains(
                "|".join(self._filter)
            )
            show_this_df = self._results[use_these_indices]

        return self.results


left, right = st.columns(2)
user_query = left.text_input("Artisanal Futures Product Search", "")
with right:
    st.markdown('')
    st.markdown('')
    button = st.button("Search")

if user_query: # they hit search
    st.session_state.result =\
        ResultState(
            prod.search(query)
        ) # overwrite, start over

selected_filters = st.multiselect(
    'Filter by principles',
    [1,2,3]
)

def etsy_views_factory(the_results: pd.DataFrame):
    default = "https://bitsofco.de/content/images/2018/12/broken-1.png"
    etsy_views = []
    for _, a_result in the_results.iterrows():
        #breakpoint()
        etsy_views.append(
            EtsyView(
                artisan=a_result['the_artisan'], craftID=a_result['craftID'], 
                url= a_result['url'],
                actual_product_image=lambda *x: a_result['image'],
                creation_information=lambda *x: a_result['principles'].split(','),
                default_product_image=default
            )
        )

    return etsy_views

#st.session_state.result.filter = selected_filters

def results_viewer(results):
    return [a_result for _, a_result in results.iterrows()]

views = etsy_views_factory(base_df)

etsy = GridViewer(views, columns_per_row=3)
etsy.draw_in_st(st)


# # Control (the GUI) allow us update_filter
# show_unfiltered_search_results()

# show_this_df = st.session_state.model.copy(deep=True)
# views = etsy_views_factory(show_this_df)

# etsy = GridViewer(views, columns_per_row=3)
# etsy.draw_in_st(st)


# def get_filters():
#     options = None
#     if st.session_state.model is not None:
#         options = set(",".join(
#             st.session_state.model.principles.values
#         ).split(','))
#     return options

# def update_model_and_filters():
#     st.session_state.model = prod.search(user_query)
#     filter = PrincipleFilterController(base_df)

#     st.session_state.filters = get_filters()
#     st.session_state.selected_filters = None

# def make_clickable(url):
#     return f'<a target="_blank" href="{url}">{url}</a>'

# def show_unfiltered_search_results():
#     with results.container():
#         st.empty()
#         show_this_df = st.session_state.model.copy(deep=True) # need to update
#         #show_this_df['url'] =\
#         #    show_this_df['url'].apply(make_clickable)

#         #etsy_views_factory(show_this_df)

#         #GridViewer(
#         #    etsy_views_factory(show_this_df)
#         #)
#         # st.write(
#         #     show_this_df[columns_to_display].to_html(escape=False),
#         #     unsafe_allow_html = True
#         # )

# def show_filtered_search_results():
#     with results.container():
#         st.empty()
#         show_this_df = base_df#st.session_state.model.copy(deep=True) # need to update

#         use_these_indices = show_this_df.principles.str.contains(
#             "|".join(selected_filters)
#         )
#         show_this_df = show_this_df[use_these_indices]

#         show_this_df['url'] =\
#             show_this_df['url'].apply(make_clickable)
#         st.write(
#             show_this_df[columns_to_display].to_html(escape=False),
#             unsafe_allow_html = True
#         )

# # The code below implements the controller
# left, right = st.columns(2)
# user_query = left.text_input("Artisanal Futures Product Search", "")
# with right:
#     st.markdown('')
#     st.markdown('')
#     button = st.button("Search")

# def actual(artisan, craftID):
#     return "https://westbh.com/images/product/b/boots-mens-rust-carpincho-chelsea-boot-256px-256px.jpg"

# def info(artisan, craftID):
#     return ['african american', 'black owned', 'women owned']

# filter = st.empty()

# if button: # they hit search
#     update_model_and_filters()
#     ## Control (the GUI) allow us update_filter
#     #show_unfiltered_search_results()

# with filter:
#     st.empty()
#     if st.session_state.filters is not None:
#         selected_filters = st.multiselect(
#             'Filter by principles',
#             st.session_state.filters
#         )
#         use_these_indices = st.session_state.model.principles.str.contains(
#             "|".join(selected_filters)
#         )
#         #show_this_df = show_this_df[use_these_indices]

#         st.session_state.model = st.session_state.model[use_these_indices]

#         if selected_filters:
#             #show_filtered_search_results()
#             pass
#         else:
#             #show_unfiltered_search_results()
#             pass

# show_this_df = st.session_state.model.copy(deep=True)
# views = etsy_views_factory(show_this_df)

# etsy = GridViewer(views, columns_per_row=3)
# etsy.draw_in_st(st)
