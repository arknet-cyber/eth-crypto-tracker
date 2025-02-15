import requests
import networkx as nx
from pyvis.network import Network
import argparse
import importlib.resources as pkg_resources
from datetime import datetime
from warnings import filterwarnings

filterwarnings('ignore', category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

class BlockchainAnalyzer:
    def __init__(self, crypto_type='btc', api_key=None):
        """Initialize with configurable API endpoints"""
        self.crypto_type = crypto_type
        self.api_key = api_key
        self.api_base = {
            'btc': 'https://api.blockcypher.com/v1/btc/main',
            'eth': 'https://api.etherscan.io/api'
        }.get(crypto_type, 'btc')
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

    def get_address_info(self, address):
        """Fetch address details from appropriate blockchain API"""
        if self.crypto_type == 'eth':
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': 10,
                'sort': 'desc',
                'apikey': self.api_key
            }
            try:
                response = requests.get(self.api_base, params=params, verify=False)
                response.raise_for_status()
                data = response.json()
                if data['status'] == '1':
                    txs = []
                    for tx in data['result']:
                        converted_tx = {
                            'hash': tx['hash'],
                            'confirmed': datetime.fromtimestamp(int(tx['timeStamp'])).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            'block_height': tx['blockNumber'],
                            'inputs': [{
                                'addresses': [tx['from']],
                                'output_value': int(tx['value'])
                            }],
                            'outputs': [{
                                'addresses': [tx['to']],
                                'value': int(tx['value'])
                            }]
                        }
                        txs.append(converted_tx)
                    return {'txs': txs}
                else:
                    print(f"Etherscan Error: {data['message']}")
                    return None
            except Exception as e:
                print(f"API Error: {str(e)}")
                return None
        else:
            url = f"{self.api_base}/addrs/{address}/full"
            try:
                response = requests.get(url, verify=False)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"API Error: {str(e)}")
                return None

    def get_transaction_graph(self, address, depth=2):
        """Build transaction graph with metadata"""
        G = nx.DiGraph()
        visited = set()

        def process_transaction(tx, current_address, current_depth):
            tx_id = self._get_node_id(tx['hash'], 'transaction')
            
            tx_time = "Unknown"
            if 'confirmed' in tx:
                try:
                    tx_time = datetime.strptime(tx['confirmed'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M")
                except:
                    tx_time = "Invalid timestamp"
            
            G.add_node(tx_id, 
                      label=str(tx_id),
                      title=f"TX: {tx['hash']}\nTime: {tx_time}\nBlock: {tx.get('block_height', 'N/A')}",
                      color='yellow',
                      shape='box')

            for inp in tx.get('inputs', []):
                if inp.get('addresses'):
                    sender = inp['addresses'][0]
                    sender_id = self._get_node_id(sender, 'address')
                    if self.crypto_type == 'btc':
                        amount = inp.get('output_value', 0) / 1e8
                        currency = 'BTC'
                    else:
                        amount = inp.get('output_value', 0) / 1e18
                        currency = 'ETH'
                    G.add_edge(sender_id, tx_id, 
                              label=f"{amount:.4f} {currency}", 
                              color='#FF0000',
                              title=f"From: {sender}\nAmount: {amount:.4f} {currency}")

            for out in tx.get('outputs', []):
                if out.get('addresses'):
                    receiver = out['addresses'][0]
                    receiver_id = self._get_node_id(receiver, 'address')
                    if self.crypto_type == 'btc':
                        amount = out.get('value', 0) / 1e8
                        currency = 'BTC'
                    else:
                        amount = out.get('value', 0) / 1e18
                        currency = 'ETH'
                    G.add_edge(tx_id, receiver_id, 
                              label=f"{amount:.4f} {currency}", 
                              color='#00FF00',
                              title=f"To: {receiver}\nAmount: {amount:.4f} {currency}")

        def recurse(current_address, current_depth):
            if current_depth > depth or current_address in visited:
                return
            visited.add(current_address)

            addr_id = self._get_node_id(current_address, 'address')
            G.add_node(addr_id, 
                      label=str(addr_id),
                      title=f"Address: {current_address}",
                      color='red' if current_depth == 0 else 'blue')

            data = self.get_address_info(current_address)
            if not data or 'txs' not in data:
                return

            for tx in data['txs'][:5]:
                try:
                    process_transaction(tx, current_address, current_depth)
                    if current_depth < depth:
                        for inp in tx.get('inputs', []):
                            if inp.get('addresses'):
                                recurse(inp['addresses'][0], current_depth + 1)
                        for out in tx.get('outputs', []):
                            if out.get('addresses'):
                                recurse(out['addresses'][0], current_depth + 1)
                except Exception as e:
                    print(f"Error processing transaction: {str(e)}")
                    continue

        recurse(address, 0)
        return G, self.legend

class Visualizer:
    @staticmethod
    def plot_interactive(graph, legend):
        """Create interactive visualization with animated connections"""
        try:
            # Initialize network with physics and interaction settings
            net = Network(height='800px', width='100%', directed=True, notebook=False)
            
            # Add nodes with click event handlers
            for node, attrs in graph.nodes(data=True):
                net.add_node(node, **attrs)
                
            # Add edges with animation properties
            for source, target, attrs in graph.edges(data=True):
                net.add_edge(source, target, 
                           **attrs,
                           dashes=True,  # Make edges dotted
                           smooth={'type': 'dynamic'})  # Enable smooth animation

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

            # Inject custom JavaScript for node click interactions
            net.set_options("""
            {
              "nodes": {
                "font": {
                  "size": 14
                }
              },
              "edges": {
                "color": {
                  "inherit": true
                },
                "smooth": {
                  "type": "dynamic"
                }
              },
              "interaction": {
                "hover": true,
                "navigationButtons": true
              },
              "physics": {
                "enabled": true,
                "barnesHut": {
                  "gravitationalConstant": -2000,
                  "centralGravity": 0.3,
                  "springLength": 95,
                  "springConstant": 0.04,
                  "damping": 0.09,
                  "avoidOverlap": 0.1
                }
              },
              "manipulation": {
                "enabled": false
              }
            }
            """)

            # Add custom JavaScript for animated connections
            net.html = net.html.replace(
                '</script>',
                """
                <script>
                function highlightConnectedNodes(nodeId) {
                    // Reset all edges
                    edges.update({
                        dashes: true,
                        color: {inherit: true}
                    });
                    
                    // Get connected edges
                    var connectedEdges = network.getConnectedEdges(nodeId);
                    
                    // Animate connected edges
                    connectedEdges.forEach(function(edgeId) {
                        edges.update({
                            id: edgeId,
                            dashes: [5, 5],
                            color: {color: '#FFA500', highlight: '#FFA500'},
                            width: 3
                        });
                    });
                }
                
                // Bind click event
                network.on("click", function(params) {
                    if (params.nodes.length > 0) {
                        highlightConnectedNodes(params.nodes[0]);
                    }
                });
                </script>
                </script>
                """
            )

            # Save and display the visualization
            net.save_graph('transaction_graph.html')
            print("\n[+] Interactive graph saved to transaction_graph.html")
            print("[+] Open transaction_graph.html in your browser to view the visualization")

        except Exception as e:
            print(f"Visualization error: {str(e)}")

def main():
    """Main function with updated argument handling"""
    parser = argparse.ArgumentParser(description='Enhanced Crypto Tracker')
    parser.add_argument('address', help='Cryptocurrency address to analyze')
    parser.add_argument('--crypto', choices=['btc', 'eth'], default='btc')
    parser.add_argument('--depth', type=int, default=2)
    parser.add_argument('--api-key', help='Etherscan API key (required for Ethereum)')
    
    args = parser.parse_args()

    if args.crypto == 'eth' and not args.api_key:
        parser.error("Ethereum analysis requires --api-key")

    analyzer = BlockchainAnalyzer(args.crypto, api_key=args.api_key)
    print(f"\n[+] Analyzing {args.address} at depth {args.depth}")
    
    transaction_graph, legend = analyzer.get_transaction_graph(args.address, args.depth)
    
    print("\n[+] Generated Node Legend:")
    for item in legend:
        print(f"Node {item['id']}: {item['label']} ({item['type']})")
    
    Visualizer.plot_interactive(transaction_graph, legend)

if __name__ == '__main__':
    main()