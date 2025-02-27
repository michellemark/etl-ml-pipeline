import sqlite3
from typing import List, Tuple

import boto3

from etl.constants import *
from etl.log_utilities import custom_logger


def ensure_data_directories_exist():
    """
    Ensure needed data directories exist.
    If directories already exist will not touch or raise errors.
    """
    os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)
    os.makedirs(GENERATED_DATA_DIR, exist_ok=True)


def create_database():
    """
    Create a new SQLite database and initialize it with defined schema.
    """
    ensure_data_directories_exist()

    try:

        with open(CREATE_TABLE_DEFINITIONS_FILE_PATH, "r") as sql_file:
            sql_script = sql_file.read()

        db_connection = sqlite3.connect(DB_LOCAL_PATH)
        db_cursor = db_connection.cursor()
        db_cursor.executescript(sql_script)
        db_connection.commit()
        db_connection.close()
        custom_logger(INFO_LOG_LEVEL, f"Database created at {DB_LOCAL_PATH}")

    except Exception as e:
        custom_logger(ERROR_LOG_LEVEL, f"Error creating the database: {str(e)}")


def insert_into_database(table_name: str, column_names: List[str], data: List[Tuple]) -> Tuple[int, int]:
    """
    Insert records into a specified SQLite database table with row-by-row error handling.

    Example Usage:
        insert_into_database(
            "properties",
            ["id", "swis_code", "print_key_code", "municipality_code"],
            [
                ("ABC 123", "ABC", "123", "XYZ"),
                ("ABD 124", "ABD", "124", "XYZ"),
                ("ACE 125", "ACE", "125", "RST"),
            ]
        )

    :param table_name: (str): Name of the target table
    :param column_names: (list of str): The list of columns to populate
    :param data: (list of tuple): List of data rows, where each row is a tuple of values
    :return: (tuple of int): A tuple containing count of rows inserted and count of rows failed.
    """
    rows_inserted: int = 0
    rows_failed: int = 0

    try:
        # Build the SQL query dynamically
        column_names_joined = ", ".join(column_names)
        value_placeholders = ", ".join(["?"] * len(column_names))
        sql_query = f"INSERT INTO {table_name} ({column_names_joined}) VALUES ({value_placeholders})"

        # Start the database connection
        with sqlite3.connect(DB_LOCAL_PATH) as db_connection:
            db_cursor = db_connection.cursor()

            # Insert each row of data one at a time so if any fail the rest will still be inserted
            for index, row in enumerate(data, start=1):

                try:
                    db_cursor.execute(sql_query, row)
                    db_connection.commit()
                    rows_inserted += 1
                except sqlite3.IntegrityError as ex:
                    custom_logger(
                        ERROR_LOG_LEVEL,
                        f"Row {index} failed to insert due to an integrity error: {ex}. Row data: {row}"
                    )
                    rows_failed += 1
                except sqlite3.Error as ex:
                    custom_logger(
                        ERROR_LOG_LEVEL,
                        f"Row {index} failed to insert due to a general database error: {ex}. Row data: {row}"
                    )
                    rows_failed += 1

        custom_logger(
            INFO_LOG_LEVEL,
            f"rows_inserted: {rows_inserted}, rows_failed: {rows_failed}"
        )

    except sqlite3.Error as ex:
        custom_logger(ERROR_LOG_LEVEL, f"Unexpected database error occurred: {ex}")
        rows_failed = len(data)

    return rows_inserted, rows_failed


def execute_select_query(query: str, params: Tuple | None = None) -> List[Tuple] | None:
    """
    Executes a raw SQL SELECT query and returns the results.

    Example Usages:
    execute_select_query("SELECT * FROM table WHERE column = value")
    execute_select_query("SELECT * FROM table WHERE column = ?", params=("value",))


    :param query: str An SQL SELECT query to execute.
    :param params: Tuple | None Optional parameters for a parameterized SELECT query.
    :return: List[Tuple] | None Query results or None if there's an error.
    """
    result = None

    try:
        with sqlite3.connect(DB_LOCAL_PATH) as db_connection:
            db_cursor = db_connection.cursor()

            if params:
                db_cursor.execute(query, params)
            else:
                db_cursor.execute(query)

            result = db_cursor.fetchall()

    except sqlite3.Error as ex:
        custom_logger(
            ERROR_LOG_LEVEL,
            f"Query {query} failed, database error: {ex}."
        )

    return result


def _get_s3_client():
    """
    Helper function to get an S3 client.
    """
    s3_client = None
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.environ.get("AWS_REGION")

    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_REGION:
        aws_session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        s3_client = aws_session.client("s3")
    else:
        if not AWS_ACCESS_KEY_ID:
            custom_logger(ERROR_LOG_LEVEL, "Missing AWS_ACCESS_KEY_ID environment variable.")
        if not AWS_SECRET_ACCESS_KEY:
            custom_logger(ERROR_LOG_LEVEL, "Missing AWS_SECRET_ACCESS_KEY environment variable.")
        if not AWS_REGION:
            custom_logger(ERROR_LOG_LEVEL, "Missing AWS_REGION environment variable.")

        custom_logger(ERROR_LOG_LEVEL, "Unable to create S3 client. Skipping operation.")

    return s3_client


def download_database_from_s3():
    """
    Downloads the SQLite database from the specified S3 bucket to the local path.
    """
    s3_client = _get_s3_client()

    if s3_client:
        ensure_data_directories_exist()

        try:
            s3_client.download_file(
                Bucket=S3_BUCKET_NAME,
                Key=SQLITE_DB_NAME,
                Filename=DB_LOCAL_PATH
            )
            custom_logger(
                INFO_LOG_LEVEL,
                f"Successfully downloaded {SQLITE_DB_NAME} from s3://{S3_BUCKET_NAME}/{SQLITE_DB_NAME} to {DB_LOCAL_PATH}")
        except Exception as ex:
            custom_logger(
                ERROR_LOG_LEVEL,
                f"Failed to download database from S3: {ex}")


def upload_database_to_s3():
    """
    Upload the SQLite database to S3, assuming needed environment variables are set.
    """
    s3_client = _get_s3_client()

    if s3_client:
        try:
            s3_client.upload_file(
                Filename=DB_LOCAL_PATH,
                Bucket=S3_BUCKET_NAME,
                Key=SQLITE_DB_NAME
            )
        except Exception as ex:
            custom_logger(
                ERROR_LOG_LEVEL,
                f"Failed to upload database to S3: {ex}")
        else:
            custom_logger(
                INFO_LOG_LEVEL,
                f"Successfully uploaded {DB_LOCAL_PATH} to s3://{S3_BUCKET_NAME}/{SQLITE_DB_NAME}")
