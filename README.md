# Installation
Download the release file from the release page and install it by pip.
Move to the directory of wingram and run the following command.
```bash
pip install .
```

Some other packages such as `bitarray` or `numpy` may be required to run this package.
Follow the error message and install the required packages.

## Download Sample Data (Optional)
A sample WIN data is provided with original WIN System software:  
https://wwweic.eri.u-tokyo.ac.jp/WIN/pub/win/

The sample data is:  
`WIN_pkg-3.0.11/etc/991109.064607`

# Usage

## Read WIN data
Give file path of WIN data 
and channel table (optionall) 
as arguments to `wingram.read` function.

```Python
import wingram

data = wingram.read('991109.064607','991109.064607.ch')
```

## Plot
To plot all traces:
```Python
data.plot()
```

To plot a specific channel, specify the index of the channel like:
```Python
data[0].plot() # Plot trace 0.
data[5:10].plot() # Plot traces from 5 to 9.
```

## Read channel table
```Python
import wingram
tbl = wingram.read_chtable('991109.064607.ch')
```

## Save as WIN data
```Python
data.write('output.win')
```

## Convert to/from obspy
```Python
st = data.to_obspy() # win to obspy
data = wingram.from_obspy(st) # obspy to win
```