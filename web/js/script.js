function goToRole(role) {
  switch (role) {
    case "admin":
      window.location.href = "pages/admin/login.html";
      break;
    case "user":
      window.location.href = "pages/user/login.html";
      break;
    case "dealer":
      window.location.href = "pages/dealer/login.html";
      break;
    default:
      alert("Invalid role selected");
  }
}