import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProducts, createProduct, deleteProduct, getLowStock, adjustStock } from '../api';

function Dashboard() {
  const [products, setProducts] = useState([]);
  const [showLowStock, setShowLowStock] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: '',
    category: '',
    fabric: '',
    color: '',
    size: '',
    price: '',
    quantity: '',
    low_stock_threshold: 5,
  });

  useEffect(() => {
    fetchProducts();
  }, [showLowStock]);

  const fetchProducts = async () => {
    try {
      const res = showLowStock ? await getLowStock() : await getProducts();
      setProducts(res.data);
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/');
      } else {
        setError('Failed to load products');
      }
    }
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await createProduct({
        ...form,
        price: parseFloat(form.price),
        quantity: parseInt(form.quantity),
        low_stock_threshold: parseInt(form.low_stock_threshold),
      });
      setForm({ name: '', category: '', fabric: '', color: '', size: '', price: '', quantity: '', low_stock_threshold: 5 });
      fetchProducts();
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      setError(`Error ${status}: ${JSON.stringify(detail)}`);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteProduct(id);
      fetchProducts();
    } catch (err) {
      setError('Failed to delete product');
    }
  };

  const handleStockChange = async (id, change) => {
    setError('');
    try {
      await adjustStock(id, change);
      fetchProducts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update stock');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/');
  };

  return (
    <div style={{ maxWidth: 900, margin: '40px auto', fontFamily: 'Arial' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h2>DrapeStudio Inventory</h2>
        <button onClick={handleLogout}>Logout</button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <h3>Add New Product</h3>
      <form onSubmit={handleAdd} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 30 }}>
        <input name="name" placeholder="Name (e.g. Banarasi Saree)" value={form.name} onChange={handleChange} required />
        <input name="category" placeholder="Category (e.g. Saree)" value={form.category} onChange={handleChange} required />
        <input name="fabric" placeholder="Fabric (e.g. Silk)" value={form.fabric} onChange={handleChange} />
        <input name="color" placeholder="Color" value={form.color} onChange={handleChange} />
        <input name="size" placeholder="Size" value={form.size} onChange={handleChange} />
        <input name="price" type="number" placeholder="Price" value={form.price} onChange={handleChange} required />
        <input name="quantity" type="number" placeholder="Starting Quantity" value={form.quantity} onChange={handleChange} required />
        <input name="low_stock_threshold" type="number" placeholder="Low Stock Alert Level" value={form.low_stock_threshold} onChange={handleChange} />
        <button type="submit" style={{ gridColumn: 'span 2' }}>Add Product</button>
      </form>

      <div style={{ marginBottom: 15 }}>
        <button onClick={() => setShowLowStock(false)} disabled={!showLowStock}>All Products</button>
        <button onClick={() => setShowLowStock(true)} disabled={showLowStock} style={{ marginLeft: 10 }}>
          Low Stock Only
        </button>
      </div>

      <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Name</th><th>Category</th><th>Fabric</th><th>Color</th><th>Size</th>
            <th>Price</th><th>Stock</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td>{p.name}</td>
              <td>{p.category}</td>
              <td>{p.fabric}</td>
              <td>{p.color}</td>
              <td>{p.size}</td>
              <td>₹{p.price}</td>
              <td>
                <button onClick={() => handleStockChange(p.id, -1)}>-</button>
                {' '}{p.quantity}{' '}
                <button onClick={() => handleStockChange(p.id, 1)}>+</button>
              </td>
              <td><button onClick={() => handleDelete(p.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Dashboard;