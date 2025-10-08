document.getElementById("btnMenu").addEventListener("click",
  function () {

    let elemento = document.getElementById("navbar");
    if (elemento.classList.contains("navbar")) {
      elemento.classList.remove("navbar");
      elemento.classList.add("no_navbar");
    } else {
      elemento.classList.remove("no_navbar");
      elemento.classList.add("navbar");
    }

  });

/*const numeroWhatsApp = "573143582372";
document.getElementById('form').addEventListener('submit', function(e) {
    e.preventDefault();
    const nombre = document.getElementById('name').value;
    const telefono = document.getElementById('phone').value;
    const correo = document.getElementById('email').value;
    const mensaje = document.getElementById('mensaje').value;

    const texto = `Hola, soy ${nombre}.\nMi número es: ${telefono}\nMi correo es: ${correo}\nMensaje: ${mensaje}`;
    const url = `https://wa.me/${numeroWhatsApp}?text=${encodeURIComponent(texto)}`;
    window.open(url, '_blank');
});
*/

window.addEventListener('scroll', function () {
  var header = document.querySelector('.header');
  header.classList.toggle('abajo', window.scrollY > 0);
})