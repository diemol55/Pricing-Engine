
import pandas as pd

def calculate_landed_cost(df, total_purchase, freight_cost, currency, exchange_rate):
    df['Purchase Cost AUD'] = df['Purchase Cost'] / exchange_rate if currency != "AUD" else df['Purchase Cost']
    if total_purchase > 0:
        df['Landed Cost AUD'] = df.apply(
            lambda row: row['Purchase Cost AUD'] + (((row['Qty'] * row['Purchase Cost']) / total_purchase) * freight_cost) / row['Qty']
            if row['Qty'] > 0 else row['Purchase Cost AUD'],
            axis=1
        )
    else:
        df['Landed Cost AUD'] = df['Purchase Cost AUD']
    return df

def lookup_rrpp_markup(cost, edited_markup):
    row = edited_markup[(edited_markup['From'] <= cost) & (cost <= edited_markup['To'])]
    return float(row['RRPP Markup'].iloc[0]) if not row.empty else 1.0

def calculate_rrpp(df, edited_markup, category_multipliers):
    df['RRPP Markup'] = df['Landed Cost AUD'].apply(lambda cost: lookup_rrpp_markup(cost, edited_markup))
    df['Category Multiplier'] = df['Category'].map(category_multipliers).fillna(1.0)
    df['RRPP'] = (df['Landed Cost AUD'] * ((df['RRPP Markup'] * df['Category Multiplier']) + 1)).round(0)
    return df

def calculate_tiered_pricing(df):
    df['Tier 1'] = df.apply(lambda row: round(row['RRPP'] * 0.95 if row['Category'] in ['Speciality Fast', 'Universal', 'Local'] else row['RRPP'] * 0.9), axis=1)
    df['Tier 2'] = df.apply(lambda row: round(row['RRPP'] * 1.37) if ((-row['RRPP'] + (row['Tier 1'] * 0.95)) / row['RRPP']) > 0.37 else round(row['Tier 1'] * 0.95), axis=1)
    df['Tier 3'] = df.apply(lambda row: round(row['RRPP'] * 1.35) if ((-row['RRPP'] + (row['Tier 2'] * 0.9)) / row['RRPP']) > 0.35 else round(row['Tier 2'] * 0.9), axis=1)
    df['Tier 4'] = df.apply(lambda row: round(row['RRPP'] * 1.3) if ((-row['RRPP'] + (row['Tier 3'] * 0.85)) / row['RRPP']) > 0.3 else round(row['Tier 3'] * 0.85), axis=1)
    df['Tier 5'] = df.apply(lambda row: round(row['RRPP'] * 1.25) if ((-row['RRPP'] + (row['Tier 4'] * 0.95)) / row['RRPP']) > 0.25 else round(row['Tier 4'] * 0.95), axis=1)
    return df
