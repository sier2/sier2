#

# A demonstration of three blocks.
# - QueryBlock emulates running a query and producing a dataframe and a column name.
# - GroupByBlock takes a dataframe and a column name, groups by the column,
#   and outputs a dataframe, a category/column name, and a count/column name.
# - BarChartBlock takes those params and draws a horizontal bar chart.

import pandas as pd
import random
import uuid

from sier2 import Block, Dag, Connection
import param

class QueryBlock(Block):
    """A block that performs a query and outputs a dataframe."""

    out_df = param.DataFrame(
        label='Dataframe',
        doc='The result of querying a large database'
    )
    out_column = param.String(
        label='Column',
        doc='The key column'
    )

    # def __init__(self, *args, **kwargs):
    #      super().__init__(*args, **kwargs)

    def query(self, sql: str):
        """Perform a query and update the output dataframe.

        This would typically be called from a GUI.
        """

        print(f'Running query in {self.__class__.__name__} ...')

        # Use this as the key column.
        # Change this value to see how it propagates.
        #
        col = 'COLOR'

        # Ignore the SQL statement and generate a random dataframe.
        # The UUID column is there to add realism.
        #
        n = random.randint(40, 80)
        print(f'  Rows returned by query: {n}')

        df = pd.DataFrame({
            col: [random.choice(['red', 'green', 'blue']) for _ in range(n)],
            'UUID': [str(uuid.uuid4()) for _ in range(n)]
        })

        self.param.update({
            'out_df': df,
            'out_column': col
        })

class GroupByBlock(Block):
    """A class that groups a dataframe by a specified column."""

    # Input params.
    #
    in_df = param.DataFrame(
        label='Input df',
        doc='A dataframe from another block'
    )
    in_column = param.String(
        label='Group column',
        doc='Name of category to group by'
    )

    # Output params.
    #
    out_group_df = param.DataFrame(
        label='Grouped df',
        doc='A grouped dataframe'
    )
    out_category = param.String(
        label='Category',
        doc='The group category (column name)'
    )
    out_count = param.String(
        label='Count',
        doc='Count of category values (column name)'
    )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def execute(self):
        """Group the COLOR column; ignore other columns."""

        print(f'Action in {self.__class__.__name__}: group by {self.in_column}')

        group_df = self.in_df.groupby(self.in_column).size().reset_index().rename(columns={0:'COUNT'})

        # Set the outputs.
        #
        self.param.update({
            'out_group_df': group_df,
            'out_category': self.in_column,
            'out_count': 'COUNT'
        })

class BarChartBlock(Block):
    """A block that draws a horizontal bar chart."""

    # Input params.
    #
    in_group_df = param.DataFrame(
        label='Grouped dataframe',
        doc='A dataframe that has been grouped'
    )
    in_category = param.String(
        label='Category',
        doc='The column containing the category values'
    )
    in_count = param.String(
        label='Count',
        doc='The column containing the count of categories'
    )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def execute(self):
        """Draw a bar chart."""

        print(f'Action in {self.__class__.__name__}: {self.in_category} vs {self.in_count}')

        if any(val is None for val in (self.in_group_df, self.in_category, self.in_count)):
            return

        # Find the maximum category name width for padding.
        #
        max_width = max(self.in_group_df[self.in_category].str.len())

        print(f'Bar chart: {self.in_category} vs {self.in_count}')
        for _, row in self.in_group_df.sort_values(by=self.in_category).reset_index().iterrows():
            cat = row[self.in_category]
            bar = '*' * row[self.in_count]
            print(f'{cat.ljust(max_width)} ({row[self.in_count]:2}): {bar}')

        print()

q = QueryBlock()
g = GroupByBlock()
b = BarChartBlock()

dag = Dag(doc='Example: bar chart', title='bar chart')
dag.connect(q, g,
    Connection('out_df', 'in_df'),
    Connection('out_column', 'in_column')
)
dag.connect(g, b,
    Connection('out_group_df', 'in_group_df'),
    Connection('out_category', 'in_category'),
    Connection('out_count', 'in_count')
)

q.query('SELECT color,count FROM the_table')
dag.execute()
