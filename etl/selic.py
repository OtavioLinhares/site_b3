
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import datetime
from datetime import timedelta
import plotly.graph_objects as go
import logging
import ipeadatapy as ip

# Configure Logging
logger = logging.getLogger("SelicETL")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

class SelicAnalyzer:
    def __init__(self):
        self.selic_series = None
        self.ibov_series = None
        self.ipca_series = None
        self.selic_trend_zones = []

    def fetch_data(self):
        logger.info("Fetching Data...")
        self.fetch_selic_bcb()
        self.fetch_ibovespa()
        
    def fetch_selic_bcb(self):
        """Fetches Selic Rate from Ipeadata (BM366_TJOVER366)."""
        try:
            logger.info("Downloading Selic (Ipeadata BM366_TJOVER366)...")
            # User requested BM366_TJOVER366
            # Returns % a.a - Taxa de juros - Over / Selic - (% a.a.)
            df_selic = ip.timeseries('BM366_TJOVER366')
            
            cols = [c for c in df_selic.columns if 'VALUE' in c]
            if not cols:
                 raise Exception("Selic Value column not found.")
            val_col = cols[0]
            
            df_selic.index = pd.to_datetime(df_selic.index)
            # Filter last 25 years
            start_date = datetime.datetime(2006, 2, 1) # Start from Feb 2006
            df_selic = df_selic[df_selic.index >= start_date]
            
            # Series is in % (e.g., 10.5). Divide by 100 for decimal representation (0.105)
            self.selic_series = df_selic[val_col] / 100.0
            
            logger.info(f"Selic data fetched: {len(self.selic_series)} records.")
            
        except Exception as e:
            logger.error(f"Error fetching Selic: {e}")
            self.selic_series = pd.Series()

    def fetch_ibovespa(self):
        try:
            logger.info("Downloading Ibovespa (Ipeadata GM366_IBVSP366)...")
            # User suggested GM366_IBVSP366
            df_ibov = ip.timeseries('GM366_IBVSP366')
            
            # Identify value column
            cols = [c for c in df_ibov.columns if 'VALUE' in c]
            if not cols:
                raise Exception("Ibov Value column not found.")
            val_col = cols[0]
            
            df_ibov.index = pd.to_datetime(df_ibov.index)
            
            # Filter last 20 years
            start_date = datetime.datetime(2006, 2, 1) # Start from Feb 2006
            df_ibov = df_ibov[df_ibov.index >= start_date]
            
            self.ibov_series = df_ibov[val_col]
            logger.info(f"Ibovespa data fetched via Ipeadata: {len(self.ibov_series)} records.")

        except Exception as e:
            logger.error(f"Error fetching Ibovespa: {e}")
            self.ibov_series = pd.Series()

    def calculate_trends(self):
        if self.selic_series is None or self.selic_series.empty:
            logger.error("No Selic data to analyze.")
            return

        logger.info("Calculating Selic Trends...")
        
        # --- User Logic Part 1: Selic Trend Zones (Binary: Up/Down) ---
        # 1. Raw Segmentation
        # Iterate and create raw zones based on direction change.
        # Treat 'Stable' as continuation of previous trend or merge later.
        
        selic_data = self.selic_series.copy().sort_index()
        raw_zones = []
        
        if len(selic_data) < 2: return
        
        current_zone_start = selic_data.index[0]
        current_zone_start_rate = selic_data.iloc[0]
        # 1 = Up, -1 = Down. 0 = Start
        current_direction = 0 
        
        # Initial pass to separate monotonic segments
        for i in range(1, len(selic_data)):
            rate = selic_data.iloc[i]
            prev_rate = selic_data.iloc[i-1]
            date = selic_data.index[i]
            prev_date = selic_data.index[i-1]
            
            diff = rate - prev_rate
            direction = 0
            if diff > 0: direction = 1
            elif diff < 0: direction = -1
            else: direction = 0 # Stable
            
            if current_direction == 0:
                if direction != 0:
                    current_direction = direction
            elif direction != 0 and direction != current_direction:
                # Direction Change
                # Close current zone
                raw_zones.append({
                    'start_date': current_zone_start,
                    'end_date': prev_date,
                    'start_rate': current_zone_start_rate,
                    'end_rate': prev_rate,
                    'trend': 'up' if current_direction == 1 else 'down'
                })
                # Start new zone
                current_zone_start = date 
                current_zone_start_rate = rate # Or prev_rate? continuity
                # Actually, for continuity, start at prev_date/rate? No, discrete points.
                # Let's say new zone starts at date (which is i).
                # But visually better if it starts where previous ended? i-1?
                # Let's restart a bit back.
                current_zone_start = prev_date
                current_zone_start_rate = prev_rate
                
                current_direction = direction

        # Close final zone
        raw_zones.append({
            'start_date': current_zone_start,
            'end_date': selic_data.index[-1],
            'start_rate': current_zone_start_rate,
            'end_rate': selic_data.iloc[-1],
            'trend': 'up' if current_direction >= 0 else 'down' # Default stable to up if at end?
        })
        
        # 2. Merge Adjacent Identical Trends (and flatten small blips if needed later)
        # This handles the "Stable" segments which didn't trigger a switch 
        # (they were absorbed into current_direction because direction==0 didn't switch it)
        
        merged_zones_1 = []
        if raw_zones:
            curr = raw_zones[0]
            for i in range(1, len(raw_zones)):
                nxt = raw_zones[i]
                if curr['trend'] == nxt['trend']:
                    curr['end_date'] = nxt['end_date']
                    curr['end_rate'] = nxt['end_rate']
                else:
                    merged_zones_1.append(curr)
                    curr = nxt
            merged_zones_1.append(curr)
            
        # 3. Apply 180 Days Rule: "se aparecer desconsiderar e considerar essa zona conforme a zona posterior"
        # Iterate until no changes to ensure propagation
        
        has_changes = True
        iterations = 0
        while has_changes and iterations < 10:
            has_changes = False
            temp_zones = []
            i = 0
            while i < len(merged_zones_1):
                curr = merged_zones_1[i]
                
                # Convert duration to days
                dur = (curr['end_date'] - curr['start_date']).days
                
                # Check if last zone? keep it
                if i == len(merged_zones_1) - 1:
                    temp_zones.append(curr)
                    i += 1
                    continue
                
                if dur < 180:
                    # Merge into Next
                    next_z = merged_zones_1[i+1]
                    # Next zone absorbs current zone's timeframe
                    next_z['start_date'] = curr['start_date']
                    next_z['start_rate'] = curr['start_rate']
                    
                    # Modify next_z in source list for continuing loop
                    merged_zones_1[i+1] = next_z
                    
                    has_changes = True
                    # Skip adding 'curr' to temp_zones, effectively deleting it
                else:
                    temp_zones.append(curr)
                i += 1
            
            if has_changes:
                merged_zones_1 = temp_zones[:]
            iterations += 1
            
        # 4. Final adjacent merge (in case absorption created adjacent same-trends)
        final_zones = []
        if merged_zones_1:
            curr = merged_zones_1[0]
            for i in range(1, len(merged_zones_1)):
                nxt = merged_zones_1[i]
                if curr['trend'] == nxt['trend']:
                    curr['end_date'] = nxt['end_date']
                    curr['end_rate'] = nxt['end_rate']
                else:
                    final_zones.append(curr)
                    curr = nxt
            final_zones.append(curr)
            
        self.selic_trend_zones = final_zones
        logger.info(f"Selic Zones identified: {len(self.selic_trend_zones)}")

        # --- User Logic Part 2: Ibovespa Correlation ---
        self.correlate_ibovespa_and_selic()

    def correlate_ibovespa_and_selic(self):
        logger.info("Correlating with Ibovespa and Calculating Selic Return...")
        
        if self.ibov_series is None: 
            return

        # Selic is daily annualized rate? 
        # Ipeadata BM366_TJOVER366 description: "Taxa de juros - Over / Selic - (% a.a.)"
        # We need to convert annual rate to daily factor if applying daily.
        # However, the series contains daily annualized rates.
        # Formula for daily factor from annual rate (assuming 252 business days):
        # factor_daily = (1 + rate_annual)^(1/252)
        # return_accum = product(factor_daily) - 1
        
        selic_full = self.selic_series.sort_index()

        for zone in self.selic_trend_zones:
            start, end = zone['start_date'], zone['end_date']
            
            # --- Ibovespa ---
            ibov_slice = self.ibov_series.loc[start:end].dropna()
            
            if ibov_slice.empty or len(ibov_slice) < 2:
                zone['ibovespa_trend'] = 'sem dados'
                zone['ibovespa_change'] = 0
            else:
                first = ibov_slice.iloc[0]
                last = ibov_slice.iloc[-1]
                change = (last - first) / first if first != 0 else 0
                zone['ibovespa_change'] = change
                
                # Simple trend classification
                if change > 0: zone['ibovespa_trend'] = 'up'
                else: zone['ibovespa_trend'] = 'down'

            # --- Selic Return ---
            # Extract Selic rates in zone
            selic_slice = selic_full.loc[start:end]
            if not selic_slice.empty:
                 # Convert annual percent to daily factor
                 # Rate is e.g. 0.1065 (10.65%). 
                 # factor = (1 + r)^(1/252)
                 factors = (1 + selic_slice) ** (1/252)
                 accumulated_factor = factors.prod()
                 selic_return = accumulated_factor - 1
                 zone['selic_return'] = selic_return
            else:
                 zone['selic_return'] = 0

            # --- Comparison for Arrows ---
            # Blue if Ibov > Selic, else Red
            if zone.get('ibovespa_change', 0) > zone.get('selic_return', 0):
                zone['performance_color'] = 'blue'
            else:
                zone['performance_color'] = 'red'

    def export_comparison_summary(self):
        # Comparison Data (Up/Down trends only)
        comparison = []
        for zone in self.selic_trend_zones:
            if zone['trend'] not in ['up', 'down']: continue
            if zone.get('ibovespa_change') is None: continue
            
            selic_change = (zone['end_rate'] - zone['start_rate']) / zone['start_rate'] if zone['start_rate'] else 0
            
            comparison.append({
                'start_date': zone['start_date'].strftime('%Y-%m-%d'),
                'end_date': zone['end_date'].strftime('%Y-%m-%d'),
                'selic_trend': zone['trend'],
                'selic_change': selic_change,
                'selic_return': zone.get('selic_return'),
                'contact_color': zone.get('performance_color')
            })
        return comparison

    def generate_html_chart(self, output_path):
        import plotly.graph_objects as go
        
        df_perf = pd.DataFrame({
            'Ibovespa': self.ibov_series,
            'Taxa Selic Anual': self.selic_series
        }).dropna()

        # Calculate Total Accumulated Returns for the entire period to include in Legend
        total_ibov_return = 0
        total_selic_return = 0
        
        if not df_perf.empty:
            total_ibov_return = (df_perf['Ibovespa'].iloc[-1] - df_perf['Ibovespa'].iloc[0]) / df_perf['Ibovespa'].iloc[0]
            # Selic Compound
            factors = (1 + df_perf['Taxa Selic Anual']) ** (1/252)
            total_selic_return = factors.prod() - 1

        # Simplify visualization loop
        fig = go.Figure()
        
        # Layout
        # Layout
        fig.update_layout(
            # title='Ibovespa e Taxa Selic Anual com Zonas de Tendência Simplificadas', # Removed title per user request
            xaxis_title='Data',
            hovermode='x unified',
            # template='plotly_white', # Removed white template
            paper_bgcolor='rgba(0,0,0,0)', # Transparent background
            plot_bgcolor='rgba(0,0,0,0)', # Transparent plot area
            font=dict(color='#e5e5e5'), # Light text for dark mode
            
            # Tooltip Styling (Fix for White on White issue)
            hoverlabel=dict(
                bgcolor="#1a1a1a",     # Dark background
                font=dict(color="white"), # White text
                bordercolor="#333"
            ),
            
            # User requested legend in bottom right corner without white box
            legend=dict(
                x=0.99, y=0.01, 
                xanchor='right', yanchor='bottom',
                bgcolor='rgba(0,0,0,0)', # Transparent
                font=dict(color='#e5e5e5')
            ),
            # Reduce Margins
            margin=dict(l=40, r=40, t=10, b=40),
            xaxis=dict(
                showgrid=True, gridcolor='#222', 
                tickfont=dict(color='#e5e5e5'), title_font=dict(color='#e5e5e5')
            ),
            yaxis=dict(
                title='Valor do Ibovespa (mil pontos)', 
                showgrid=True, gridcolor='#222',
                title_font=dict(color='#6c8dd9'), # Muted Blue accent
                tickfont=dict(color='#e5e5e5')
            ),
            yaxis2=dict(
                title='Taxa Selic Anual (%)', 
                overlaying='y', side='right', 
                tickformat='.2%', 
                showgrid=False, 
                title_font=dict(color='#ff8a80'), # Muted Red accent
                tickfont=dict(color='#e5e5e5')
            )
        )
        
        # Zones
        # Colors based on Selic Trend: Down=Blue, Up=Red
        # User requested darker background colors previously, but now "contraste exagerado".
        # Reducing opacity for a more "sober" look.
        # Down (Selic Falling) -> Blue | Up (Selic Rising) -> Red
        color_map = {'down': 'rgba(0, 0, 255, 0.1)', 'up': 'rgba(255, 0, 0, 0.1)', 'stable': 'rgba(128, 128, 128, 0.05)'}
        
        # Muted Colors for arrows and text to be less "aggressive"
        # Blue: #4b6cb7 -> #6c8dd9 (Lighter/Muted)
        # Red: #ef5350 -> #ff8a80 (Lighter/Muted)
        muted_blue = '#6c8dd9'
        muted_red = '#ff8a80'
        
        for i, zone in enumerate(self.selic_trend_zones):
            fill = color_map.get(zone['trend'], 'rgba(0,0,0,0)')
            fig.add_vrect(x0=zone['start_date'], x1=zone['end_date'], fillcolor=fill, layer="below", line_width=0)
            
            # Arrows
            if zone.get('ibovespa_change') is not None:
                start, end = zone['start_date'], zone['end_date']
                # Get approximate values
                try:
                    # Find closest dates in ibov series
                    val_start = self.ibov_series.asof(start)
                    val_end = self.ibov_series.asof(end)
                    
                    if pd.notna(val_start) and pd.notna(val_end):
                        # Determine color based on original logic but use muted palette
                        # If perf color was originally set in analysis, map it
                        raw_color = zone.get('performance_color', 'gray')
                        arrow_color = muted_blue if raw_color == 'blue' else muted_red if raw_color == 'red' else 'gray'
                        
                        # Thicker arrows
                        fig.add_annotation(
                            x=end, y=val_end, xref="x", yref="y1",
                            ax=start, ay=val_start, axref="x", ayref="y1",
                            text='', showarrow=True, arrowcolor=arrow_color, arrowwidth=3, arrowhead=2
                        )
                        
                        # Add Text Label (centered in time, vertically centered in plot)
                        # Midpoint Time
                        mid_date = start + (end - start) / 2
                        
                        ibov_pct = zone.get('ibovespa_change', 0) * 100
                        selic_pct = zone.get('selic_return', 0) * 100
                        
                        label_text = f"<b>Ibov: {ibov_pct:+.1f}%</b><br>Selic: {selic_pct:+.1f}%"
                        
                        # Stagger logic (Alternating heights to avoid overlap)
                        # Use index i to alternate: 0.95, 0.82, 0.95, 0.82...
                        # Keeping it near the top as requested "sempre +/- no topo"
                        y_pos = 0.98 if i % 2 == 0 else 0.85
                        
                        fig.add_annotation(
                            x=mid_date, y=y_pos, xref="x", yref="paper", 
                            text=label_text,
                            showarrow=False,
                            font=dict(color='white', size=11), # Explicit white text
                            bgcolor='rgba(0,0,0,0)' # Transparent
                        )

                except Exception:
                    pass

        # Traces with Total Returns in Legend
        # Multiply by 100 for correct percentage display
        name_ibov = f"Ibovespa (Total: {total_ibov_return * 100:+.1f}%)"
        name_selic = f"Selic (Total: {total_selic_return * 100:+.1f}%)"

        fig.add_trace(go.Scatter(x=df_perf.index, y=df_perf['Ibovespa'], name=name_ibov, mode='lines', line=dict(color='#6c8dd9', width=2), yaxis='y1'))
        fig.add_trace(go.Scatter(x=df_perf.index, y=df_perf['Taxa Selic Anual'], name=name_selic, mode='lines', line=dict(color='#ff8a80', width=2, dash='dot'), yaxis='y2'))
        
        # Save
        # Save with CDN to reduce file size (Fix for deployment timeout/failure)
        fig.write_html(output_path, include_plotlyjs='cdn', config={'responsive': True})
        logger.info(f"Chart saved to {output_path}")

# Standalone execution
if __name__ == "__main__":
    analyzer = SelicAnalyzer()
    analyzer.fetch_data()
    analyzer.calculate_trends()
    
    # Export summary
    import json
    summary = analyzer.export_comparison_summary()
    with open("data/selic_summary.json", "w") as f:
        json.dump(summary, f, indent=4)
        
    # Generate Chart
    analyzer.generate_html_chart("web/public/selic_analysis.html")
    print("Execution Complete.")
