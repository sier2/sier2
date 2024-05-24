#

# A demonstration of three gizmos.
# - QueryGizmo emulates running a query and producing a dataframe and a column name.
# - GroupByGizmo takes a dataframe and a column name, groups by the column,
#   and outputs a dataframe, a category/column name, and a count/column name.
# - BarChartGizmo takes those params and draws a horizontal bar chart.

import pandas as pd
import random
import uuid

from gizmo import Gizmo, GizmoManager
import param

class QueryGizmo(Gizmo):
    """A gizmo that performs a query and outputs a dataframe."""

    df = param.DataFrame(
        label='Dataframe',
        doc='The result of querying a large database'
    )
    column = param.String(
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
            'df': df,
            'column': col
        })

class GroupByGizmo(Gizmo):
    """A class that groups a dataframe by a specified column."""

    # Input params.
    #
    df = param.DataFrame(
        label='Input df',
        doc='A dataframe from another gizmo',
        allow_refs=True
    )
    column = param.String(
        label='Group column',
        doc='Name of category to group by',
        allow_refs=True
    )

    # Output params.
    #
    group_df = param.DataFrame(
        label='Grouped df',
        doc='A grouped dataframe'
    )
    category = param.String(
        label='Category',
        doc='The group category (column name)'
    )
    count = param.String(
        label='Count',
        doc='Count of category values (column name)'
    )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def execute(self):
        """Group the COLOR column; ignore other columns."""

        print(f'Action in {self.__class__.__name__}: group by {self.column}')

        group_df = self.df.groupby(self.column).size().reset_index().rename(columns={0:'COUNT'})

        # Set the outputs.
        #
        self.param.update({
            'group_df': group_df,
            'category': self.column,
            'count': 'COUNT'
        })

class BarChartGizmo(Gizmo):
    """A gizmo that draws a horizontal bar chart."""

    # Input params.
    #
    group_df = param.DataFrame(
        label='Grouped dataframe',
        doc='A dataframe that has been grouped',
        allow_refs=True
    )
    category = param.String(
        label='Category',
        doc='The column containing the category values',
        allow_refs=True
    )
    count = param.String(
        label='Count',
        doc='The column containing the count of categories',
        allow_refs=True
    )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def execute(self):
        """Draw a bar chart."""

        print(f'Action in {self.__class__.__name__}: {self.category} vs {self.count}')

        if any(val is None for val in (self.group_df, self.category, self.count)):
            return

        # Find the maximum category name width for padding.
        #
        max_width = max(self.group_df[self.category].str.len())

        print(f'Bar chart: {self.category} vs {self.count}')
        for _, row in self.group_df.sort_values(by=self.category).reset_index().iterrows():
            cat = row[self.category]
            bar = '*' * row[self.count]
            print(f'{cat.ljust(max_width)} ({row[self.count]:2}): {bar}')

        print()

def main():
    """Pretend to be a gizmo manager."""

    q = QueryGizmo()
    g = GroupByGizmo()
    GizmoManager.connect(q, g, ['df', 'column'])

    b = BarChartGizmo()
    GizmoManager.connect(g, b, ['group_df', 'category', 'count'])

    while input('Enter to run a query; q to quit:').strip().lower()[:1]!='q':
        # Give the query gizmo something to do,
        # and watch the result cascade through the grouping to the chart.
        #
        q.query('SELECT color,count FROM the_table')

    return q, g, b

if __name__=='__main__':
    q, g, b = main()
