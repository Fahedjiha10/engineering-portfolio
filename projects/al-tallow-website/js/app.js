/**
 * Simple cart (localStorage) + drawer UI.
 * Replace CHECKOUT_URL with your Stripe Payment Link / Shopify checkout URL.
 */
const CHECKOUT_URL = "https://example.com/checkout"; // TODO: replace

const cartKey = "al_tallow_cart_v1";

function readCart(){
  try { return JSON.parse(localStorage.getItem(cartKey)) ?? []; }
  catch(e){ return []; }
}
function writeCart(items){
  localStorage.setItem(cartKey, JSON.stringify(items));
  renderCartBadge();
}
function addToCart(item){
  const cart = readCart();
  // merge same variant
  const idx = cart.findIndex(x => x.sku === item.sku);
  if(idx >= 0){
    cart[idx].qty += item.qty;
  }else{
    cart.push(item);
  }
  writeCart(cart);
}
function removeFromCart(sku){
  const cart = readCart().filter(x => x.sku !== sku);
  writeCart(cart);
  renderCartDrawer();
}
function cartCount(){
  return readCart().reduce((s,x)=>s + (x.qty||0), 0);
}
function cartSubtotal(){
  return readCart().reduce((s,x)=>s + (x.qty||0) * (x.price||0), 0);
}
function money(n){
  return new Intl.NumberFormat(undefined, {style:"currency", currency:"USD"}).format(n);
}

function renderCartBadge(){
  document.querySelectorAll("[data-cart-count]").forEach(el=>{
    const n = cartCount();
    el.textContent = String(n);
    el.style.display = n>0 ? "inline-block" : "none";
  });
}

function openCart(){
  const drawer = document.getElementById("cartDrawer");
  if(!drawer) return;
  drawer.classList.add("open");
  renderCartDrawer();
}
function closeCart(){
  const drawer = document.getElementById("cartDrawer");
  if(!drawer) return;
  drawer.classList.remove("open");
}
function renderCartDrawer(){
  const itemsWrap = document.getElementById("cartItems");
  const totalEl = document.getElementById("cartTotal");
  const checkoutBtn = document.getElementById("checkoutBtn");
  if(!itemsWrap || !totalEl || !checkoutBtn) return;

  const cart = readCart();
  itemsWrap.innerHTML = "";

  if(cart.length === 0){
    itemsWrap.innerHTML = `<div class="muted">Your cart is empty.</div>`;
    totalEl.textContent = money(0);
    checkoutBtn.disabled = true;
    checkoutBtn.setAttribute("aria-disabled","true");
    return;
  }

  cart.forEach(item=>{
    const row = document.createElement("div");
    row.className = "cart-item";
    row.innerHTML = `
      <div>
        <div class="title">${escapeHtml(item.name)}</div>
        <div class="meta">${escapeHtml(item.variant)} · Qty ${item.qty}</div>
        <div class="meta">${money(item.price)} each</div>
      </div>
      <div style="display:flex; flex-direction:column; gap:6px; align-items:flex-end">
        <div class="title">${money(item.price * item.qty)}</div>
        <button type="button" data-remove="${escapeAttr(item.sku)}">Remove</button>
      </div>
    `;
    itemsWrap.appendChild(row);
  });

  itemsWrap.querySelectorAll("[data-remove]").forEach(btn=>{
    btn.addEventListener("click", ()=> removeFromCart(btn.getAttribute("data-remove")));
  });

  totalEl.textContent = money(cartSubtotal());
  checkoutBtn.disabled = false;
  checkoutBtn.removeAttribute("aria-disabled");
}

function goCheckout(){
  // For a real store: use Shopify Buy Button / Stripe Checkout session.
  window.location.href = CHECKOUT_URL;
}

function escapeHtml(str){
  return String(str)
    .replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}
function escapeAttr(str){
  return escapeHtml(str).replaceAll("`","&#096;");
}

document.addEventListener("DOMContentLoaded", ()=>{
  renderCartBadge();

  document.querySelectorAll("[data-open-cart]").forEach(btn=>{
    btn.addEventListener("click", openCart);
  });
  document.querySelectorAll("[data-close-cart]").forEach(btn=>{
    btn.addEventListener("click", closeCart);
  });

  const checkoutBtn = document.getElementById("checkoutBtn");
  if(checkoutBtn) checkoutBtn.addEventListener("click", goCheckout);

  // Add-to-cart buttons
  document.querySelectorAll("[data-add-to-cart]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      const sku = btn.getAttribute("data-sku");
      const name = btn.getAttribute("data-name");
      const variant = btn.getAttribute("data-variant");
      const price = Number(btn.getAttribute("data-price"));
      const qtyInputId = btn.getAttribute("data-qty-input");
      let qty = 1;
      if(qtyInputId){
        const el = document.getElementById(qtyInputId);
        if(el) qty = Math.max(1, Number(el.value || 1));
      }
      addToCart({ sku, name, variant, price, qty });
      openCart();
    });
  });
});
