"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################


@app.route("/accounts", methods=["GET"])
def list_accounts():
    """
        Lists accounts
        This endpoints lists all accounts stored in the database
    """
    app.logger.info("Request to list all accounts recieved")
    # use the Account.all() method to retrieve all accounts
    accounts = Account.all()

    # create a list of serialize() accounts
    response = [account.serialize() for account in accounts]

    # log the number of accounts being returned in the list
    app.logger.info(f"Returning a list of {len(response)} accounts")

    # return the list with a return code of status.HTTP_200_OK
    return jsonify(response), status.HTTP_200_OK

######################################################################
# READ AN ACCOUNT
######################################################################


@app.route("/accounts/<id>", methods=["GET"])
def read_account(id):
    """
        Reads an account
        This endpoint returns a single account given a valid account id
    """
    app.logger.info(f"Received request to read Account #{id}")
    account = Account.find(id)
    if not account:
        abort(status.HTTP_404_NOT_FOUND, f"Account {id} not found")
    return account.serialize(), status.HTTP_200_OK

######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################


@app.route("/accounts/<int:id>", methods=["PUT"])
def update_account(id):
    """
        Updates an Account.
        This endpoint, given a properly formed Account object with an exitsing id,
        updated the passed Account on the database.
    """
    app.logger.info(f"Request to update Account #{id} recieved")

    # use the Account.find() method to retrieve the account by the account_id
    account = Account.find(id)
    # abort() with a status.HTTP_404_NOT_FOUND if it cannot be found
    if not account:
        abort(status.HTTP_404_NOT_FOUND, "Account could not be found")

    # call the deserialize() method on the account passing in request.get_json()
    try:
        account.deserialize(request.get_json())
    except KeyError:
        abort(status.HTTP_400_BAD_REQUEST, "Account Data invalid")

    # call account.update() to update the account with the new data
    app.logger.info(f"Updating Account #{id}")
    account.update()

    # return the serialize() version of the account with a return code of status.HTTP_200_OK
    return account.serialize(), status.HTTP_200_OK

######################################################################
# DELETE AN ACCOUNT
######################################################################


@app.route("/accounts/<int:id>", methods=["DELETE"])
def delete_account(id):
    """
        Delete an Account
        This endpoint will delete the requested account by ID if the account exists
    """
    account = Account.find(id)
    if account:
        account.delete()
    return "", status.HTTP_204_NO_CONTENT

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )