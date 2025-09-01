# pages/soccer/bankroll_tracking.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.helpers import format_currency, calculate_roi, get_profit_loss
import config

# pages/cricket/bankroll_tracking.py  
def show():
    """Cricket bankroll tracking"""
    import streamlit as st
    st.markdown("""
    <div class="main-header">
        <h1>Cricket Bankroll Management</h1>
        <p>Track cricket betting performance across all formats</p>
    </div>
    """, unsafe_allow_html=True)
    
    display_bankroll_overview()
    
    st.subheader("Bankroll Settings")
    manage_bankroll()
    
    from database.db_manager import DatabaseManager
    db_manager = DatabaseManager()
    
    st.subheader("Cricket Performance Analytics")
    display_performance_charts('cricket', db_manager)
    
    st.subheader("Cricket Betting History")
    display_betting_history('cricket', db_manager)
    
    st.subheader("Cricket Risk Analysis")
    display_risk_metrics('cricket', db_manager)

def display_bankroll_overview():
    """Display bankroll overview metrics"""
    
    current_bankroll = st.session_state.get('bankroll', config.DEFAULT_BANKROLL)
    initial_bankroll = st.session_state.get('initial_bankroll', config.DEFAULT_BANKROLL)
    
    roi = calculate_roi()
    profit_loss = get_profit_loss()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Bankroll",
            format_currency(current_bankroll),
            delta=format_currency(profit_loss) if profit_loss != 0 else None
        )
    
    with col2:
        st.metric("Initial Bankroll", format_currency(initial_bankroll))
    
    with col3:
        roi_color = "normal" if roi == 0 else "inverse" if roi < 0 else "off"
        st.metric("Total ROI", f"{roi:.2f}%", delta=None)
    
    with col4:
        st.metric(
            "Total P&L",
            format_currency(profit_loss),
            delta=None
        )

def manage_bankroll():
    """Bankroll management interface"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Update Bankroll**")
        new_bankroll = st.number_input(
            "New Bankroll Amount:",
            value=float(st.session_state.get('bankroll', config.DEFAULT_BANKROLL)),
            min_value=0.0,
            step=1.0,
            key="new_bankroll_input"
        )
        
        if st.button("Update Bankroll", type="primary"):
            old_bankroll = st.session_state.get('bankroll', config.DEFAULT_BANKROLL)
            change = new_bankroll - old_bankroll
            
            st.session_state.bankroll = new_bankroll
            
            # Record bankroll change
            try:
                db_manager = DatabaseManager()
                db_manager.save_bankroll_change(
                    amount=new_bankroll,
                    change_amount=change,
                    change_type='manual_adjustment',
                    description=f"Manual bankroll update from {format_currency(old_bankroll)}"
                )
            except Exception as e:
                st.error(f"Error saving bankroll change: {e}")
            
            st.success(f"Bankroll updated to {format_currency(new_bankroll)}")
            st.rerun()
    
    with col2:
        st.markdown("**Reset Options**")
        
        if st.button("Reset to Initial Bankroll", type="secondary"):
            initial = st.session_state.get('initial_bankroll', config.DEFAULT_BANKROLL)
            old_bankroll = st.session_state.get('bankroll', config.DEFAULT_BANKROLL)
            change = initial - old_bankroll
            
            st.session_state.bankroll = initial
            
            try:
                db_manager = DatabaseManager()
                db_manager.save_bankroll_change(
                    amount=initial,
                    change_amount=change,
                    change_type='manual_adjustment',
                    description="Reset to initial bankroll"
                )
            except Exception as e:
                st.error(f"Error saving reset: {e}")
            
            st.success(f"Bankroll reset to {format_currency(initial)}")
            st.rerun()
        
        if st.button("Set New Initial Bankroll"):
            current = st.session_state.get('bankroll', config.DEFAULT_BANKROLL)
            st.session_state.initial_bankroll = current
            st.success(f"Initial bankroll set to {format_currency(current)}")
            st.rerun()

def display_performance_charts(sport, db_manager):
    """Display performance visualization charts"""
    
    try:
        # Get betting history
        bet_history = db_manager.get_bet_history(sport=sport, limit=100)
        
        if bet_history.empty:
            st.info("No betting history available yet. Place some bets to see performance analytics.")
            return
        
        # Convert timestamp
        bet_history['timestamp'] = pd.to_datetime(bet_history['timestamp'])
        bet_history = bet_history.sort_values('timestamp')
        
        # Bankroll performance over time
        fig_bankroll = go.Figure()
        
        fig_bankroll.add_trace(go.Scatter(
            x=bet_history['timestamp'],
            y=bet_history['bankroll_after'],
            mode='lines+markers',
            name='Bankroll',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        ))
        
        # Add initial bankroll line
        initial_bankroll = st.session_state.get('initial_bankroll', config.DEFAULT_BANKROLL)
        fig_bankroll.add_hline(
            y=initial_bankroll,
            line_dash="dash",
            line_color="gray",
            annotation_text="Initial Bankroll"
        )
        
        fig_bankroll.update_layout(
            title="Bankroll Performance Over Time",
            xaxis_title="Date",
            yaxis_title="Bankroll ($)",
            height=400
        )
        
        st.plotly_chart(fig_bankroll, use_container_width=True)
        
        # Win/Loss distribution
        col1, col2 = st.columns(2)
        
        with col1:
            # Results breakdown
            settled_bets = bet_history[bet_history['result'].isin(['win', 'loss'])]
            
            if not settled_bets.empty:
                result_counts = settled_bets['result'].value_counts()
                
                fig_pie = px.pie(
                    values=result_counts.values,
                    names=result_counts.index,
                    title="Win/Loss Distribution",
                    color_discrete_map={'win': '#2ca02c', 'loss': '#d62728'}
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Profit/Loss by market type
            if not settled_bets.empty:
                market_pnl = settled_bets.groupby('market_type')['profit_loss'].sum().reset_index()
                
                fig_bar = px.bar(
                    market_pnl,
                    x='market_type',
                    y='profit_loss',
                    title="P&L by Market Type",
                    color='profit_loss',
                    color_continuous_scale='RdYlGn'
                )
                fig_bar.update_layout(xaxis_title="Market Type", yaxis_title="Profit/Loss ($)")
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Stake size distribution
        fig_stakes = px.histogram(
            bet_history,
            x='stake',
            nbins=20,
            title="Stake Size Distribution",
            color_discrete_sequence=['#1f77b4']
        )
        fig_stakes.update_layout(xaxis_title="Stake Size ($)", yaxis_title="Frequency")
        st.plotly_chart(fig_stakes, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating performance charts: {e}")
        st.info("Charts will appear after placing bets.")

def display_betting_history(sport, db_manager):
    """Display recent betting history"""
    
    try:
        bet_history = db_manager.get_bet_history(sport=sport, limit=20)
        
        if bet_history.empty:
            st.info("No betting history available.")
            return
        
        # Format the dataframe for display
        display_df = bet_history.copy()
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['stake'] = display_df['stake'].apply(lambda x: f"${x:.2f}")
        display_df['profit_loss'] = display_df['profit_loss'].apply(lambda x: f"${x:.2f}")
        display_df['odds'] = display_df['odds'].apply(lambda x: f"{'+' if x > 0 else ''}{x}")
        
        # Select columns to display
        columns_to_show = [
            'timestamp', 'bet_type', 'market_type', 'odds', 'stake', 'result', 'profit_loss'
        ]
        
        st.dataframe(
            display_df[columns_to_show],
            use_container_width=True,
            hide_index=True
        )
        
    except Exception as e:
        st.error(f"Error loading betting history: {e}")

def display_risk_metrics(sport, db_manager):
    """Display risk management metrics"""
    
    try:
        betting_stats = db_manager.get_betting_stats(sport=sport)
        
        if betting_stats['total_bets'] == 0:
            st.info("No completed bets to analyze risk metrics.")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bets", betting_stats['total_bets'])
            st.metric("Win Rate", f"{betting_stats['win_rate']:.1f}%")
        
        with col2:
            st.metric("Total Wins", betting_stats['total_wins'])
            st.metric("Total Losses", betting_stats['total_losses'])
        
        with col3:
            st.metric("Average Stake", format_currency(betting_stats['average_stake']))
            st.metric("Average Odds", f"{'+' if betting_stats['average_odds'] > 0 else ''}{betting_stats['average_odds']:.0f}")
        
        with col4:
            roi_value = betting_stats['roi']
            roi_color = "normal" if roi_value == 0 else "inverse" if roi_value < 0 else "off"
            st.metric("ROI", f"{roi_value:.2f}%")
            st.metric("Total P&L", format_currency(betting_stats['total_profit_loss']))
        
        # Risk assessment
        st.markdown("### Risk Assessment")
        
        current_bankroll = st.session_state.get('bankroll', config.DEFAULT_BANKROLL)
        avg_stake_percent = (betting_stats['average_stake'] / current_bankroll) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Position Sizing Analysis**")
            st.write(f"Average stake: {avg_stake_percent:.1f}% of bankroll")
            
            if avg_stake_percent > 10:
                st.warning("⚠️ HIGH RISK: Average stakes exceed 10% of bankroll")
            elif avg_stake_percent > 5:
                st.info("📊 MEDIUM RISK: Stakes between 5-10% of bankroll")
            else:
                st.success("✅ LOW RISK: Conservative stake sizing")
        
        with col2:
            st.markdown("**Performance Assessment**")
            
            if betting_stats['win_rate'] > 55 and betting_stats['roi'] > 5:
                st.success("🎯 PROFITABLE: Strong performance metrics")
            elif betting_stats['win_rate'] > 45 and betting_stats['roi'] > -5:
                st.info("📈 BREAK-EVEN: Stable performance")
            else:
                st.error("📉 LOSING: Review strategy needed")
        
        # Kelly Criterion adherence
        st.markdown("### Kelly Criterion Adherence")
        
        bet_history = db_manager.get_bet_history(sport=sport, limit=50)
        if not bet_history.empty:
            avg_kelly = bet_history['kelly_fraction'].mean()
            avg_stake_actual = (bet_history['stake'] / current_bankroll * 100).mean()
            
            kelly_adherence = min(100, (avg_kelly / max(avg_stake_actual, 0.1)) * 100)
            
            st.metric("Kelly Adherence", f"{kelly_adherence:.0f}%")
            
            if kelly_adherence > 80:
                st.success("Excellent Kelly Criterion following")
            elif kelly_adherence > 60:
                st.info("Good Kelly discipline")
            else:
                st.warning("Consider improving Kelly adherence")
    
    except Exception as e:
        st.error(f"Error calculating risk metrics: {e}")


