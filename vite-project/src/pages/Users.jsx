import { useCallback, useEffect, useState } from "react";

function Users({ user }) {
  const API_URL = "http://127.0.0.1:8000";

  const [users, setUsers] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [showModal, setShowModal] = useState(false);

  const [editingUser, setEditingUser] = useState(null);

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "quality_engineer",
  });

  const [saving, setSaving] = useState(false);


 

  const fetchUsers = useCallback(async () => {
    try {
      setError("");

      const token =
        localStorage.getItem("access_token");

      if (!token) {
        setError(
          "You are not logged in."
        );

        setLoading(false);

        return;
      }

      const response = await fetch(
        `${API_URL}/users`,
        {
          method: "GET",

          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to load users."
        );
      }

      setUsers(data);

    } catch (err) {

      console.error(
        "Users fetch error:",
        err
      );

      setError(
        err.message ||
          "Failed to load users."
      );

    } finally {

      setLoading(false);
    }
  }, []);


 

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);




  const handleChange = (event) => {

    const {
      name,
      value,
    } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };


 

  const openCreateModal = () => {

    setEditingUser(null);

    setFormData({
      name: "",
      email: "",
      password: "",
      role: "quality_engineer",
    });

    setShowModal(true);

    setError("");
  };


  // =========================================================
  // OPEN EDIT MODAL
  // =========================================================

  const openEditModal = (selectedUser) => {

    setEditingUser(selectedUser);

    setFormData({
      name: selectedUser.name || "",
      email: selectedUser.email || "",
      password: "",
      role:
        selectedUser.role ||
        "quality_engineer",
    });

    setShowModal(true);

    setError("");
  };


  // =========================================================
  // CLOSE MODAL
  // =========================================================

  const closeModal = () => {

    if (saving) {
      return;
    }

    setShowModal(false);

    setEditingUser(null);
  };


  // =========================================================
  // SAVE USER
  // =========================================================

  const handleSubmit = async (event) => {

    event.preventDefault();

    setSaving(true);

    setError("");

    try {

      const token =
        localStorage.getItem("access_token");

      if (!token) {
        throw new Error(
          "You are not logged in."
        );
      }


      // =====================================================
      // EDIT USER
      // =====================================================

      if (editingUser) {

        const response = await fetch(
          `${API_URL}/users/${editingUser.id}`,
          {
            method: "PUT",

            headers: {
              Authorization: `Bearer ${token}`,

              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              name: formData.name,
              email: formData.email,
              role: formData.role,
            }),
          }
        );

        const data =
          await response.json();

        if (!response.ok) {

          throw new Error(
            data?.detail ||
              "Failed to update user."
          );
        }

      }

      // =====================================================
      // CREATE USER
      // =====================================================

      else {

        if (!formData.password) {

          throw new Error(
            "Password is required."
          );
        }

        const response = await fetch(
          `${API_URL}/users`,
          {
            method: "POST",

            headers: {
              Authorization: `Bearer ${token}`,

              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              name: formData.name,
              email: formData.email,
              password: formData.password,
              role: formData.role,
            }),
          }
        );

        const data =
          await response.json();

        if (!response.ok) {

          throw new Error(
            data?.detail ||
              "Failed to create user."
          );
        }
      }


      // =====================================================
      // REFRESH USERS
      // =====================================================

      await fetchUsers();

      setShowModal(false);

      setEditingUser(null);

    } catch (err) {

      console.error(
        "User save error:",
        err
      );

      setError(
        err.message ||
          "Failed to save user."
      );

    } finally {

      setSaving(false);
    }
  };


  // =========================================================
  // DELETE USER
  // =========================================================

  const handleDelete = async (selectedUser) => {

    if (
      selectedUser.id === user?.id
    ) {

      alert(
        "You cannot delete your own account."
      );

      return;
    }


    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedUser.name}?`
    );

    if (!confirmed) {
      return;
    }


    try {

      const token =
        localStorage.getItem("access_token");

      const response = await fetch(
        `${API_URL}/users/${selectedUser.id}`,
        {
          method: "DELETE",

          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data =
        await response.json();

      if (!response.ok) {

        throw new Error(
          data?.detail ||
            "Failed to delete user."
        );
      }

      await fetchUsers();

    } catch (err) {

      console.error(
        "Delete user error:",
        err
      );

      setError(
        err.message ||
          "Failed to delete user."
      );
    }
  };


  // =========================================================
  // FORMAT ROLE
  // =========================================================

  const formatRole = (role) => {

    if (
      role ===
      "quality_engineer"
    ) {

      return "Quality Engineer";
    }

    if (
      role ===
      "factory_supervisor"
    ) {

      return "Factory Supervisor";
    }

    return role
      ?.replaceAll("_", " ")
      ?.replace(
        /\b\w/g,
        (char) =>
          char.toUpperCase()
      );
  };


  // =========================================================
  // FORMAT DATE
  // =========================================================

  const formatDate = (date) => {

    if (!date) {
      return "-";
    }

    return new Date(date).toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  };


  // =========================================================
  // SEARCH
  // =========================================================

  const filteredUsers =
    users.filter((item) => {

      const searchValue =
        search
          .trim()
          .toLowerCase();

      if (!searchValue) {
        return true;
      }

      return (
        item.name
          ?.toLowerCase()
          .includes(searchValue) ||

        item.email
          ?.toLowerCase()
          .includes(searchValue) ||

        item.role
          ?.toLowerCase()
          .includes(searchValue)
      );
    });


  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {

    return (
      <div className="w-full">

        <div className="mb-6">

          <h1 className="text-2xl font-bold text-slate-900">
            Users
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Manage system users.
          </p>

        </div>

        <div className="flex min-h-[350px] items-center justify-center rounded-xl border border-slate-200 bg-white shadow-sm">

          <div className="text-center">

            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

            <p className="mt-4 text-sm text-slate-500">
              Loading users...
            </p>

          </div>

        </div>

      </div>
    );
  }


  // =========================================================
  // PAGE
  // =========================================================

  return (
    <div className="w-full">

      {/* =====================================================
          HEADER
         ===================================================== */}

      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">

        <div>

          <h1 className="text-2xl font-bold text-slate-900">
            Users
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Manage system users and their roles.
          </p>

        </div>


        <button
          type="button"
          onClick={openCreateModal}
          className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
        >
          + Add User
        </button>

      </div>


      {/* =====================================================
          ERROR
         ===================================================== */}

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4">

          <p className="text-sm font-medium text-red-700">
            {error}
          </p>

        </div>
      )}


      {/* =====================================================
          SEARCH
         ===================================================== */}

      <div className="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">

        <input
          type="text"
          value={search}
          onChange={(event) =>
            setSearch(event.target.value)
          }
          placeholder="Search by name, email or role..."
          className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />

      </div>


      {/* =====================================================
          USER TABLE
         ===================================================== */}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[800px]">

            <thead className="border-b border-slate-200 bg-slate-50">

              <tr>

                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  ID
                </th>

                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  User
                </th>

                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Email
                </th>

                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Role
                </th>

                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Created
                </th>

                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Actions
                </th>

              </tr>

            </thead>


            <tbody className="divide-y divide-slate-100">

              {filteredUsers.length === 0 ? (

                <tr>

                  <td
                    colSpan="6"
                    className="px-6 py-12 text-center"
                  >

                    <p className="text-sm text-slate-500">
                      No users found.
                    </p>

                  </td>

                </tr>

              ) : (

                filteredUsers.map(
                  (item) => (

                    <tr
                      key={item.id}
                      className="transition hover:bg-slate-50"
                    >

                      {/* ID */}

                      <td className="px-6 py-4 text-sm font-medium text-slate-700">
                        #{item.id}
                      </td>


                      {/* USER */}

                      <td className="px-6 py-4">

                        <div className="flex items-center gap-3">

                          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-700">

                            {item.name
                              ?.charAt(0)
                              ?.toUpperCase() ||
                              "U"}

                          </div>

                          <div>

                            <p className="text-sm font-semibold text-slate-900">
                              {item.name}
                            </p>

                            {item.id ===
                              user?.id && (
                              <p className="text-xs text-blue-600">
                                You
                              </p>
                            )}

                          </div>

                        </div>

                      </td>


                      {/* EMAIL */}

                      <td className="px-6 py-4 text-sm text-slate-600">
                        {item.email}
                      </td>


                      {/* ROLE */}

                      <td className="px-6 py-4">

                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                            item.role ===
                            "factory_supervisor"
                              ? "bg-purple-100 text-purple-700"
                              : "bg-blue-100 text-blue-700"
                          }`}
                        >
                          {formatRole(
                            item.role
                          )}
                        </span>

                      </td>


                      {/* DATE */}

                      <td className="px-6 py-4 text-sm text-slate-500">
                        {formatDate(
                          item.created_at
                        )}
                      </td>


                      {/* ACTIONS */}

                      <td className="px-6 py-4">

                        <div className="flex justify-end gap-2">

                          <button
                            type="button"
                            onClick={() =>
                              openEditModal(
                                item
                              )
                            }
                            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            disabled={
                              item.id ===
                              user?.id
                            }
                            onClick={() =>
                              handleDelete(
                                item
                              )
                            }
                            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
                          >
                            Delete
                          </button>

                        </div>

                      </td>

                    </tr>
                  )
                )
              )}

            </tbody>

          </table>

        </div>

      </div>


      {/* =====================================================
          USER COUNT
         ===================================================== */}

      <div className="mt-4 text-xs text-slate-400">

        Showing {filteredUsers.length} of{" "}
        {users.length} users

      </div>


      {/* =====================================================
          CREATE / EDIT MODAL
         ===================================================== */}

      {showModal && (

        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 px-4">

          <div className="w-full max-w-lg rounded-2xl bg-white shadow-xl">

            {/* MODAL HEADER */}

            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">

              <div>

                <h2 className="text-lg font-bold text-slate-900">

                  {editingUser
                    ? "Edit User"
                    : "Add User"}

                </h2>

                <p className="mt-1 text-xs text-slate-500">

                  {editingUser
                    ? "Update user information."
                    : "Create a new system user."}

                </p>

              </div>


              <button
                type="button"
                onClick={closeModal}
                className="text-xl text-slate-400 transition hover:text-slate-700"
              >
                ×
              </button>

            </div>


            {/* FORM */}

            <form
              onSubmit={handleSubmit}
              className="space-y-5 p-6"
            >

              {/* NAME */}

              <div>

                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Name
                </label>

                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  placeholder="Enter full name"
                />

              </div>


              {/* EMAIL */}

              <div>

                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Email
                </label>

                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  placeholder="Enter email address"
                />

              </div>


              {/* PASSWORD */}

              {!editingUser && (

                <div>

                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    Password
                  </label>

                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    minLength="6"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    placeholder="Enter password"
                  />

                </div>

              )}


              {/* ROLE */}

              <div>

                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Role
                </label>

                <select
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                >

                  <option value="quality_engineer">
                    Quality Engineer
                  </option>

                  <option value="factory_supervisor">
                    Factory Supervisor
                  </option>

                </select>

              </div>


              {/* BUTTONS */}

              <div className="flex justify-end gap-3 border-t border-slate-100 pt-5">

                <button
                  type="button"
                  onClick={closeModal}
                  disabled={saving}
                  className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >

                  {saving
                    ? "Saving..."
                    : editingUser
                      ? "Update User"
                      : "Create User"}

                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </div>
  );
}

export default Users;