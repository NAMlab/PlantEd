import pandas as pd
import sys

# assume your data is stored in a DataFrame called df
# with a datetime column called 'date_time'

# convert the datetime column to DatetimeIndex

def check_missing_rows(df, filename):
	df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M')
	df.set_index('date', inplace=True)
	# create a new DataFrame with a complete set of timestamps
	min_timestamp = df.index.min().floor('H')
	max_timestamp = df.index.max().ceil('H')
	print(min_timestamp)
	print(max_timestamp)
	all_timestamps = pd.date_range(min_timestamp, max_timestamp, freq='H')
	all_data = pd.DataFrame(index=all_timestamps)
	print(df)
	print(all_data)

	# merge the two DataFrames
	merged_data = pd.merge(all_data, df, left_index=True, right_index=True, how='left')

	# check for missing entries
	missing_entries = merged_data[merged_data.isnull().any(axis=1)]
	if len(missing_entries) > 0:
	    print("Missing entries:")
	    print(missing_entries)
	    merged_data.fillna(0, inplace=True)
	    print(merged_data)
	    merged_data.to_csv('cleaned_'+filename)
	    print("Missing entries got filled and saved")
	else:
	    print("No missing entries.")
	    
def main(filename):  
	df = pd.read_csv(filename)
	check_missing_rows(df, filename)
	

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0])
