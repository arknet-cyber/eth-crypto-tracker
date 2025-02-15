import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import networkx as nx
from pyvis.network import Network

# Configuration
API_KEY = "K94JA6NRE2VX1UM1U7FJYTZ8UIBNN1DEWF"

# Updated list of mixer addresses (verified as of 2023)
MIXER_ADDRESSES = [
    # Tornado Cash (Sanctioned)
    "0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc",  # 0.1 ETH
    "0x47CE0C6eD5B0Ce3d3A51fdb1C52DC66a7c3c2936",  # 1 ETH
    "0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF",  # 10 ETH
    "0xA160cdAB225685dA1d56aa342Ad8841c3b53f291",  # 100 ETH
    "0x23773E65ed146A459791799d01336DB287f25334",  # DAI
    "0x722122dF12D4e14e13Ac3b6895a86e84145b6967",  # USDC
    
    # Other Mixers
    "0x94Be88213a387E992Dd87DE56950a9aef34b9448",  # Blender.io (Sanctioned)
    "0x8576acc5c05d6ce88f4e49bf65bdf0c62f91353c",  # ChipMixer
    "0x538Ab2E4eF7C6aC90bC4684890927fBDF069A5A5",  # Wasabi Wallet
]

# Major exchange hot wallet addresses
EXCHANGE_ADDRESSES = [
    # Binance
    "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE",
    "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549",
    "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8",
    
    # Coinbase
    "0xA090e606E30bD747d4E6245a1517EbE430F0057e",
    "0x4f3a120e72c76c22ae802d129f599bfdbc31cb81",
    "0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98",
    
    # Kraken
    "0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2",
    "0x0d0707963952f2fBA59dD06f2b425ace40b492Fe",
    
    # OKX
    "0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b",
    "0x236f9f97e0E62388479bf9E5BA2CA76A2F41fAb3",
    
    # Bitfinex
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "0x876EabF441B2EE5B5b0554Fd502a8E0600950cFa",
    
    # Huobi
    "0xdc76cd25977e0a5ae17155770273ad58648900d3",
    "0xadb2b42f6bd96f5c65920b9ac88619dce4166f94",
    
    # Crypto.com
    "0x6262998Ced04146fA42253a5C0AF90CA02dfd2A3",
    "0x46340b20830761efd32832a74d7169b29feb9758",
    
    # FTX (Bankruptcy Estate)
    "0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2",
    "0xC098B2a3Aa256D2140208C3de6543aAEf5cd3A94",
]

def get_transactions(address):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data["result"] if data["status"] == "1" else []

def analyze_transactions(transactions, address):
    df = pd.DataFrame(transactions)
    if df.empty:
        return df, [], []
    
    # Convert values and types
    df['value_eth'] = df['value'].astype(float) / 10**18
    df['timestamp'] = pd.to_datetime(df['timeStamp'], unit='s')
    
    # Normalize addresses
    address = address.lower()
    df['from'] = df['from'].str.lower()
    df['to'] = df['to'].str.lower()
    exchange_addrs = [a.lower() for a in EXCHANGE_ADDRESSES]
    mixer_addrs = [a.lower() for a in MIXER_ADDRESSES]
    
    # Detect interactions
    exchange_txs = df[df['to'].isin(exchange_addrs)]
    mixer_txs = df[df['to'].isin(mixer_addrs)]
    
    return df, exchange_txs, mixer_txs

class GraphVisualizer:
    def __init__(self):
        self.node_counter = 0
        self.node_map = {}
        self.legend = []

    def _get_node_id(self, identifier, label_type):
        """Create consistent node IDs with labels"""
        if identifier not in self.node_map:
            self.node_counter += 1
            self.node_map[identifier] = self.node_counter
            self.legend.append({
                'id': self.node_counter,
                'label': f"{self.node_counter}: {identifier[:6]}...{identifier[-4:]}",
                'type': label_type
            })
        return self.node_map[identifier]

    def create_transaction_graph(self, transactions, address):
        """Build transaction graph with metadata"""
        G = nx.DiGraph()
        address = address.lower()

        for tx in transactions:
            try:
                tx_hash = tx['hash']
                from_addr = tx['from'].lower()
                to_addr = tx['to'].lower()
                value_eth = int(tx['value']) / 1e18
                timestamp = datetime.fromtimestamp(int(tx['timeStamp'])).strftime("%Y-%m-%d %H:%M:%S")

                # Transaction node
                tx_id = self._get_node_id(tx_hash, 'transaction')
                G.add_node(tx_id,
                          label=str(tx_id),
                          title=f"Tx: {tx_hash}\nValue: {value_eth:.4f} ETH\nTime: {timestamp}",
                          color='yellow',
                          shape='box',
                          size=25)

                # From address node
                from_id = self._get_node_id(from_addr, 'address')
                G.add_node(from_id,
                          label=str(from_id),
                          title=f"Sender: {from_addr}",
                          color='red' if from_addr == address else 'blue',
                          size=30 if from_addr == address else 25)

                # To address node
                to_id = self._get_node_id(to_addr, 'address')
                G.add_node(to_id,
                          label=str(to_id),
                          title=f"Receiver: {to_addr}",
                          color='red' if to_addr == address else 'blue',
                          size=30 if to_addr == address else 25)

                # Edges
                G.add_edge(from_id, tx_id, value=value_eth, color='#FF0000',
                          title=f"Sent {value_eth:.4f} ETH", arrows='to', dashes=True)
                G.add_edge(tx_id, to_id, value=value_eth, color='#00FF00',
                          title=f"Received {value_eth:.4f} ETH", arrows='to', dashes=True)
            except Exception as e:
                print(f"Error processing transaction: {str(e)}")
                continue

        return G, self.legend

    def visualize_graph(self, G, legend):
        """Create interactive visualization with animated connections"""
        try:
            net = Network(height='800px', width='100%', directed=True, notebook=False)
            net.from_nx(G)
            
            # Add legend
            legend_html = "<h3>Node Legend:</h3><ul>"
            for item in legend:
                legend_html += f"<li><b>{item['id']}</b>: {item['label']} ({item['type']})</li>"
            legend_html += "</ul>"
            
            net.add_node("legend", 
                        label="Node Legend",
                        title=legend_html,
                        color='#FFFFFF',
                        shape='box',
                        x=0,
                        y=0,
                        fixed=True)

            # Configure visualization settings
            net.set_options("""
            {
              "nodes": {
                "font": {
                  "size": 14,
                  "face": "arial"
                },
                "scaling": {
                  "min": 10,
                  "max": 40
                }
              },
              "edges": {
                "arrows": {
                  "to": {
                    "enabled": true,
                    "scaleFactor": 0.8
                  }
                },
                "smooth": {
                  "type": "dynamic"
                },
                "dashes": true,
                "scaling": {
                  "min": 0.5,
                  "max": 4
                }
              },
              "physics": {
                "barnesHut": {
                  "gravitationalConstant": -2000,
                  "centralGravity": 0.3,
                  "springLength": 200,
                  "damping": 0.09
                },
                "minVelocity": 0.75
              },
              "interaction": {
                "hover": true,
                "navigationButtons": true
              }
            }
            """)

            # Save and return HTML
            net.save_graph('graph.html')
            with open('graph.html', 'r', encoding='utf-8') as f:
                html = f.read()
            return html

        except Exception as e:
            print(f"Visualization error: {str(e)}")
            return ""

def main():
    st.set_page_config(page_title="Advanced Crypto Analyzer", layout="wide")
    st.title("🕵️♂️ Advanced Crypto Transaction Investigator")
    
    # Sidebar controls
    with st.sidebar:
        st.header("🔧 Settings")
        address = st.text_input("Ethereum Address", "0x...")
        api_key = st.text_input("Etherscan API Key", API_KEY, type="password")
        update_btn = st.button("Analyze Transactions")
        
        st.markdown("### 🎯 Tracking Parameters")
        st.markdown("**Tracked Mixers:**")
        st.code(f"{len(MIXER_ADDRESSES)} known privacy tools")
        st.markdown("**Tracked Exchanges:**")
        st.code(f"{len(EXCHANGE_ADDRESSES)} major platforms")

    if update_btn and address and api_key:
        with st.spinner("🕵️♂️ Investigating blockchain activity..."):
            transactions = get_transactions(address)
            
        if not transactions:
            st.error("🚨 No transactions found or invalid API key")
            return

        df, exchange_txs, mixer_txs = analyze_transactions(transactions, address)

        # Summary Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transactions", len(df))
        col2.metric("Exchange Interactions", len(exchange_txs), 
                   "⚠️ Cash Out Detected" if len(exchange_txs) > 0 else "✅ Clean")
        col3.metric("Mixer Interactions", len(mixer_txs), 
                   "⛔ Privacy Alert" if len(mixer_txs) > 0 else "✅ Clean")

        # Visualization Section
        st.subheader("📈 Transaction Pattern Analysis")
        
        # Timeline Chart
        fig1 = px.timeline(df, 
                          x_start="timestamp", 
                          x_end="timestamp",
                          y="value_eth",
                          color_discrete_sequence=['#FF4B4B'],
                          title="Transaction Value Timeline",
                          labels={"value_eth": "ETH Value", "timestamp": "Date"},
                          height=400)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Risk Distribution Chart
        fig2 = px.pie(names=['Regular', 'Exchange', 'Mixer'], 
                     values=[len(df)-len(exchange_txs)-len(mixer_txs), 
                            len(exchange_txs), 
                            len(mixer_txs)],
                     title="Transaction Type Distribution",
                     color_discrete_sequence=['green', 'orange', 'red'])
        st.plotly_chart(fig2, use_container_width=True)

        # Transaction Flow Visualization
        st.subheader("🔗 Transaction Flow Graph")
        with st.spinner("Generating interactive visualization..."):
            visualizer = GraphVisualizer()
            G, legend = visualizer.create_transaction_graph(transactions, address)
            html = visualizer.visualize_graph(G, legend)
            st.components.v1.html(html, width=1200, height=800)

        # Detailed Findings
        st.subheader("🔍 Detailed Findings")
        
        if not exchange_txs.empty:
            with st.expander("⚠️ Exchange Cash-Out Transactions", expanded=True):
                st.dataframe(exchange_txs[['hash', 'to', 'value_eth', 'timestamp']], 
                           column_config={
                               "hash": "Tx Hash",
                               "to": "Exchange Address",
                               "value_eth": "Value (ETH)",
                               "timestamp": "Date"
                           }, height=250)
                
        if not mixer_txs.empty:
            with st.expander("⛔ Privacy Mixer Transactions", expanded=True):
                st.dataframe(mixer_txs[['hash', 'to', 'value_eth', 'timestamp']],
                           column_config={
                               "hash": "Tx Hash",
                               "to": "Mixer Address",
                               "value_eth": "Value (ETH)",
                               "timestamp": "Date"
                           }, height=250)

        # Raw Data Explorer
        with st.expander("📁 Full Transaction History", expanded=False):
            st.dataframe(df[['hash', 'from', 'to', 'value_eth', 'timestamp']],
                       column_config={
                           "hash": "Tx Hash",
                           "from": "Sender",
                           "to": "Receiver",
                           "value_eth": "Value (ETH)",
                           "timestamp": "Date"
                       }, height=500)

if __name__ == "__main__":
    main()