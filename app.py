from shiny import App, render, ui, reactive
import pandas as pd
import matplotlib.ticker as mtick

sales_data = pd.read_excel("Adidas_US_Sales_Datasets.xlsx")
sales_data = sales_data.iloc[3:, 1:]
column_names = pd.Series(sales_data.iloc[0, ])
for i in range(0, len(sales_data.columns)): 
    sales_data = sales_data.rename(columns = {sales_data.columns[i] : column_names.iloc[i]})
sales_data = sales_data.iloc[1:, ]

sales_data = sales_data.astype({'Retailer' : 'str', 'Retailer ID' : 'int32', 'Invoice Date' : 'datetime64[ns]',
     'State' : 'str', 'City' : 'str', 'Product' : 'str', 'Price per Unit' : 'int32', 'Units Sold' : 'int32',
     'Total Sales' : 'int32', 'Operating Profit' : 'int32', 'Operating Margin' : 'float',
     'Sales Method' : 'str'})

app_ui = ui.page_fluid(
    ui.panel_title("Adidas Sales"),
    ui.layout_columns(
        ui.input_select("retailer_select", "Choose a retailer:", sorted(sales_data['Retailer'].drop_duplicates()), selected = "Walmart"),
        ui.input_date_range("daterange", "Date Range", start=min(sales_data['Invoice Date']), end=max(sales_data['Invoice Date']))
    ),
    ui.row(
    ui.column(6, ui.output_plot("barchart")),
    ui.column(6, ui.output_plot("piechart"))
    ),
    ui.navset_card_tab(
        ui.nav_panel("Daily View", ui.output_plot("sales_daily")), 
        ui.nav_panel("Monthly View", ui.output_plot("sales_monthly")),
        ui.nav_panel("Quarterly View", ui.output_plot("sales_quarterly")),
        id = "tab",
        
    ),
    ui.output_table("data")
)

def server(input, output, session):
    @reactive.Calc
    def dataset():
        selected_retailer = input.retailer_select() 
        first_date = pd.to_datetime(input.daterange()[0])
        last_date = pd.to_datetime(input.daterange()[1])
        filtered_sales_dataset = sales_data[sales_data['Retailer'] == selected_retailer]
        filtered_sales_dataset = filtered_sales_dataset[(filtered_sales_dataset['Invoice Date'] >= first_date) &
        (filtered_sales_dataset['Invoice Date'] <= last_date)]
        return filtered_sales_dataset

    @reactive.Calc
    def grouped_by_region_data():
        sales_by_region = dataset().groupby(['Region']).agg(sales = ('Total Sales', 'sum'))
        return sales_by_region

    @reactive.Calc
    def total_dales_daily():
        sales_daily = dataset().groupby(dataset()['Invoice Date'])['Total Sales'].sum()
        return sales_daily
    
    @reactive.Calc
    def total_sales_monthly():
        sales_monthly = dataset().groupby(dataset()['Invoice Date'].dt.to_period("M"))['Total Sales'].sum()
        return sales_monthly
    
    @reactive.Calc
    def total_sales_quarterly():
        sales_quarterly = dataset().groupby(dataset()['Invoice Date'].dt.to_period("Q"))['Total Sales'].sum()
        return sales_quarterly

    @render.plot
    def barchart():
        if not grouped_by_region_data().empty:
            sales_by_region = grouped_by_region_data()
            ax = sales_by_region.plot(kind='bar', title = 'Total Sales by Region', legend = False)
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
            for container in ax.containers:
                ax.bar_label(container, labels=[f"{v/1000:.1f}K" for v in container.datavalues])
            return ax 
    
    @render.plot
    def piechart():
        if not grouped_by_region_data().empty:
            sales_by_region_perc = grouped_by_region_data()/grouped_by_region_data().sum()
            ax = sales_by_region_perc.plot.pie(y='sales', legend = 'True', autopct='%1.1f%%' )
            return ax
    
    @render.plot
    def sales_daily():
        if not total_dales_daily().empty:
            sales = total_dales_daily()
            ax = sales.plot(kind = "line", title = "Total Sales by Invoice Date", grid = True)
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
            return ax

    @render.plot
    def sales_monthly():
        if not total_sales_monthly().empty:
            sales = total_sales_monthly()
            ax = sales.plot(kind = "line", title = "Total Sales monthly", grid = True)
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
            return ax

    @render.plot
    def sales_quarterly():
        if not total_sales_quarterly().empty:
            sales = total_sales_quarterly()
            ax = sales.plot(kind = "line", title = "Total Sales quarterly", grid = True)
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
            return ax

    @render.table
    def data():
        return dataset().sort_values(by='Invoice Date').head()


app = App(app_ui, server)